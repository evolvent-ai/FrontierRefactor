/* Serve a C subject over the wire. Written into the task; not required by the factory.
 *
 * The subject supplies, in a translation unit compiled alongside this one:
 *
 *     const char *entry(const char *args_json);   / * the arguments, as a JSON array * /
 *     char *entry_error;                          / * why it refused, or NULL * /
 *
 * `entry` returns a malloc'd JSON document, which this file frees. To refuse, it returns NULL and
 * leaves a message in `entry_error`; the message stays the subject's own, and is only read here,
 * never freed, so a static string is a perfectly good thing to put there. `entry_error` is cleared
 * before every call, so a stale message cannot be reported against a later request. A refusal is an
 * answer: it is reported as {"ok":false,"error":...} and the loop carries on reading. C has no
 * exception type to name, so the message is the whole of the error text, where the shims for
 * languages that do have one prefix a type name.
 *
 * WHY THERE IS A JSON PARSER IN HERE. C has no JSON and these tasks run in an offline container
 * with no libraries to link against, so the wire's own codec has to be part of the shim. It parses
 * the grammar rather than splitting on punctuation, because the arguments it has to read include
 * strings containing braces, commas and escaped quotes.
 */
#define _POSIX_C_SOURCE 200809L

#include <math.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

extern const char *entry(const char *args_json);
extern char *entry_error;

/* A line from the wire is nested only as deeply as the arguments are, and a limit keeps a
 * pathological line from running the stack out of this recursive-descent parser. */
#define MAX_DEPTH 200

enum json_kind {
    JSON_NULL, JSON_BOOL, JSON_NUMBER, JSON_STRING, JSON_ARRAY, JSON_OBJECT
};

typedef struct json {
    enum json_kind kind;
    int boolean;
    double number;
    char *string;                  /* JSON_STRING: NUL-terminated, owned */
    struct json **items;           /* JSON_ARRAY and JSON_OBJECT: the values, owned */
    char **keys;                   /* JSON_OBJECT: parallel to items, owned */
    size_t count;
    size_t capacity;
} Json;

/* A growable byte buffer. `ok` goes to zero on the first allocation failure and every later append
 * is a no-op, so the appends themselves need no error checking and the one check that matters
 * happens where the buffer is finally used. */
typedef struct {
    char *data;
    size_t len;
    size_t cap;
    int ok;
} Buf;

static void buf_init(Buf *b)
{
    b->data = NULL;
    b->len = 0;
    b->cap = 0;
    b->ok = 1;
}

static void buf_free(Buf *b)
{
    free(b->data);
    buf_init(b);
}

static void buf_reserve(Buf *b, size_t extra)
{
    size_t want;
    char *grown;

    if (!b->ok) {
        return;
    }
    if (extra > (size_t)-1 - b->len - 1) {
        b->ok = 0;                                  /* the length would wrap */
        return;
    }
    want = b->len + extra + 1;                      /* room for the NUL as well */
    if (want <= b->cap) {
        return;
    }
    while (b->cap < want) {
        b->cap = b->cap ? b->cap * 2 : 64;
    }
    grown = realloc(b->data, b->cap);
    if (grown == NULL) {
        b->ok = 0;
        return;
    }
    b->data = grown;
    /* Terminate immediately rather than leaving that to buf_append.
     *
     * A buffer that is reserved and never appended to is a real case: an empty JSON string reserves
     * nought bytes and returns the buffer as it stands. Without this line that buffer is
     * uninitialised heap -- or, after a realloc, whatever was there before -- and every reader
     * walks it until it happens on a zero byte. It does not crash; it silently substitutes garbage
     * for "", so a probe containing an empty string freezes an expectation against data that was
     * never sent, and the value differs from one run to the next. */
    b->data[b->len] = '\0';
}

static void buf_append(Buf *b, const char *text, size_t len)
{
    buf_reserve(b, len);
    if (!b->ok) {
        return;
    }
    memcpy(b->data + b->len, text, len);
    b->len += len;
    b->data[b->len] = '\0';
}

static void buf_puts(Buf *b, const char *text)
{
    buf_append(b, text, strlen(text));
}

static void buf_putc(Buf *b, char c)
{
    buf_append(b, &c, 1);
}

static Json *json_new(enum json_kind kind)
{
    Json *node = calloc(1, sizeof *node);

    if (node != NULL) {
        node->kind = kind;
    }
    return node;
}

static void json_free(Json *node)
{
    size_t i;

    if (node == NULL) {
        return;
    }
    free(node->string);
    for (i = 0; i < node->count; i++) {
        if (node->keys != NULL) {
            free(node->keys[i]);
        }
        json_free(node->items[i]);
    }
    free(node->items);
    free(node->keys);
    free(node);
}

/* Take ownership of `key` and `value`; on failure both are released here, so a caller can hand
 * them over and forget about them either way. */
static int json_push(Json *node, char *key, Json *value)
{
    if (value == NULL) {
        free(key);
        return 0;
    }
    if (node->count == node->capacity) {
        size_t cap = node->capacity ? node->capacity * 2 : 8;
        Json **items = realloc(node->items, cap * sizeof *items);
        if (items == NULL) {
            free(key);
            json_free(value);
            return 0;
        }
        node->items = items;
        if (node->kind == JSON_OBJECT) {
            char **keys = realloc(node->keys, cap * sizeof *keys);
            if (keys == NULL) {
                free(key);
                json_free(value);
                return 0;
            }
            node->keys = keys;
        }
        node->capacity = cap;
    }
    if (node->kind == JSON_OBJECT) {
        node->keys[node->count] = key;
    } else {
        free(key);
    }
    node->items[node->count] = value;
    node->count++;
    return 1;
}

static const Json *json_get(const Json *node, const char *key)
{
    size_t i;

    if (node == NULL || node->kind != JSON_OBJECT) {
        return NULL;
    }
    for (i = 0; i < node->count; i++) {
        if (strcmp(node->keys[i], key) == 0) {
            return node->items[i];
        }
    }
    return NULL;
}

typedef struct {
    const unsigned char *p;
    const unsigned char *end;
} Parser;

static Json *parse_value(Parser *s, int depth);

static void skip_space(Parser *s)
{
    while (s->p < s->end && (*s->p == ' ' || *s->p == '\t' || *s->p == '\n' || *s->p == '\r')) {
        s->p++;
    }
}

static int parse_literal(Parser *s, const char *word)
{
    size_t len = strlen(word);

    if ((size_t)(s->end - s->p) < len || memcmp(s->p, word, len) != 0) {
        return 0;
    }
    s->p += len;
    return 1;
}

/* Encode one code point as UTF-8 into a string buffer. */
static void put_utf8(Buf *b, unsigned long cp)
{
    if (cp < 0x80UL) {
        buf_putc(b, (char)cp);
    } else if (cp < 0x800UL) {
        buf_putc(b, (char)(0xC0 | (cp >> 6)));
        buf_putc(b, (char)(0x80 | (cp & 0x3F)));
    } else if (cp < 0x10000UL) {
        buf_putc(b, (char)(0xE0 | (cp >> 12)));
        buf_putc(b, (char)(0x80 | ((cp >> 6) & 0x3F)));
        buf_putc(b, (char)(0x80 | (cp & 0x3F)));
    } else {
        buf_putc(b, (char)(0xF0 | (cp >> 18)));
        buf_putc(b, (char)(0x80 | ((cp >> 12) & 0x3F)));
        buf_putc(b, (char)(0x80 | ((cp >> 6) & 0x3F)));
        buf_putc(b, (char)(0x80 | (cp & 0x3F)));
    }
}

static int parse_hex4(Parser *s, unsigned long *out)
{
    unsigned long value = 0;
    int i;

    if (s->end - s->p < 4) {
        return 0;
    }
    for (i = 0; i < 4; i++) {
        unsigned char c = s->p[i];
        value <<= 4;
        if (c >= '0' && c <= '9') {
            value |= (unsigned long)(c - '0');
        } else if (c >= 'a' && c <= 'f') {
            value |= (unsigned long)(c - 'a' + 10);
        } else if (c >= 'A' && c <= 'F') {
            value |= (unsigned long)(c - 'A' + 10);
        } else {
            return 0;
        }
    }
    s->p += 4;
    *out = value;
    return 1;
}

/* -> a malloc'd NUL-terminated string, or NULL. */
static char *parse_string_raw(Parser *s)
{
    Buf out;

    if (s->p >= s->end || *s->p != '"') {
        return NULL;
    }
    s->p++;
    buf_init(&out);
    buf_reserve(&out, 0);                           /* an empty string still needs its NUL */
    while (s->p < s->end) {
        unsigned char c = *s->p++;

        if (c == '"') {
            if (!out.ok) {
                break;
            }
            return out.data;
        }
        if (c < 0x20) {
            break;                                  /* a raw control byte is not a JSON string */
        }
        if (c != '\\') {
            buf_putc(&out, (char)c);
            continue;
        }
        if (s->p >= s->end) {
            break;
        }
        switch (*s->p++) {
        case '"':  buf_putc(&out, '"');  break;
        case '\\': buf_putc(&out, '\\'); break;
        case '/':  buf_putc(&out, '/');  break;
        case 'b':  buf_putc(&out, '\b'); break;
        case 'f':  buf_putc(&out, '\f'); break;
        case 'n':  buf_putc(&out, '\n'); break;
        case 'r':  buf_putc(&out, '\r'); break;
        case 't':  buf_putc(&out, '\t'); break;
        case 'u': {
            unsigned long first;
            if (!parse_hex4(s, &first)) {
                goto broken;
            }
            /* The factory encodes with Python's default ensure_ascii, so everything above the BMP
             * arrives as a surrogate pair and the halves have to be rejoined here. */
            if (first >= 0xD800UL && first < 0xDC00UL) {
                unsigned long second;
                if (s->end - s->p < 2 || s->p[0] != '\\' || s->p[1] != 'u') {
                    goto broken;
                }
                s->p += 2;
                if (!parse_hex4(s, &second) || second < 0xDC00UL || second >= 0xE000UL) {
                    goto broken;
                }
                first = 0x10000UL + ((first - 0xD800UL) << 10) + (second - 0xDC00UL);
            } else if (first >= 0xDC00UL && first < 0xE000UL) {
                goto broken;                        /* a low surrogate with no high one */
            }
            put_utf8(&out, first);
            break;
        }
        default:
            goto broken;
        }
    }

broken:
    buf_free(&out);
    return NULL;
}

static Json *parse_string(Parser *s)
{
    char *text = parse_string_raw(s);
    Json *node;

    if (text == NULL) {
        return NULL;
    }
    node = json_new(JSON_STRING);
    if (node == NULL) {
        free(text);
        return NULL;
    }
    node->string = text;
    return node;
}

static Json *parse_number(Parser *s)
{
    const unsigned char *start = s->p;
    char text[64];
    size_t len;
    Json *node;

    if (s->p < s->end && *s->p == '-') {
        s->p++;
    }
    while (s->p < s->end && *s->p >= '0' && *s->p <= '9') {
        s->p++;
    }
    if (s->p < s->end && *s->p == '.') {
        s->p++;
        while (s->p < s->end && *s->p >= '0' && *s->p <= '9') {
            s->p++;
        }
    }
    if (s->p < s->end && (*s->p == 'e' || *s->p == 'E')) {
        s->p++;
        if (s->p < s->end && (*s->p == '+' || *s->p == '-')) {
            s->p++;
        }
        while (s->p < s->end && *s->p >= '0' && *s->p <= '9') {
            s->p++;
        }
    }
    len = (size_t)(s->p - start);
    if (len == 0 || len >= sizeof text) {
        return NULL;
    }
    memcpy(text, start, len);
    text[len] = '\0';
    node = json_new(JSON_NUMBER);
    if (node == NULL) {
        return NULL;
    }
    node->number = strtod(text, NULL);
    return node;
}

static Json *parse_array(Parser *s, int depth)
{
    Json *node = json_new(JSON_ARRAY);

    if (node == NULL) {
        return NULL;
    }
    s->p++;                                         /* the '[' */
    skip_space(s);
    if (s->p < s->end && *s->p == ']') {
        s->p++;
        return node;
    }
    for (;;) {
        if (!json_push(node, NULL, parse_value(s, depth + 1))) {
            goto broken;
        }
        skip_space(s);
        if (s->p >= s->end) {
            goto broken;
        }
        if (*s->p == ',') {
            s->p++;
            continue;
        }
        if (*s->p == ']') {
            s->p++;
            return node;
        }
        goto broken;
    }

broken:
    json_free(node);
    return NULL;
}

static Json *parse_object(Parser *s, int depth)
{
    Json *node = json_new(JSON_OBJECT);

    if (node == NULL) {
        return NULL;
    }
    s->p++;                                         /* the '{' */
    skip_space(s);
    if (s->p < s->end && *s->p == '}') {
        s->p++;
        return node;
    }
    for (;;) {
        char *key;

        skip_space(s);
        key = parse_string_raw(s);
        if (key == NULL) {
            goto broken;
        }
        skip_space(s);
        if (s->p >= s->end || *s->p != ':') {
            free(key);
            goto broken;
        }
        s->p++;
        if (!json_push(node, key, parse_value(s, depth + 1))) {
            goto broken;
        }
        skip_space(s);
        if (s->p >= s->end) {
            goto broken;
        }
        if (*s->p == ',') {
            s->p++;
            continue;
        }
        if (*s->p == '}') {
            s->p++;
            return node;
        }
        goto broken;
    }

broken:
    json_free(node);
    return NULL;
}

static Json *parse_value(Parser *s, int depth)
{
    if (depth > MAX_DEPTH) {
        return NULL;
    }
    skip_space(s);
    if (s->p >= s->end) {
        return NULL;
    }
    switch (*s->p) {
    case 'n':
        return parse_literal(s, "null") ? json_new(JSON_NULL) : NULL;
    case 't': {
        Json *node;
        if (!parse_literal(s, "true")) {
            return NULL;
        }
        node = json_new(JSON_BOOL);
        if (node != NULL) {
            node->boolean = 1;
        }
        return node;
    }
    case 'f':
        return parse_literal(s, "false") ? json_new(JSON_BOOL) : NULL;
    case '"':
        return parse_string(s);
    case '[':
        return parse_array(s, depth);
    case '{':
        return parse_object(s, depth);
    default:
        if (*s->p == '-' || (*s->p >= '0' && *s->p <= '9')) {
            return parse_number(s);
        }
        return NULL;
    }
}

/* Read one complete JSON value and insist it is the whole of the text. */
static Json *json_parse(const char *text, size_t len)
{
    Parser s;
    Json *node;

    s.p = (const unsigned char *)text;
    s.end = s.p + len;
    node = parse_value(&s, 0);
    if (node == NULL) {
        return NULL;
    }
    skip_space(&s);
    if (s.p != s.end) {
        json_free(node);
        return NULL;
    }
    return node;
}

static void write_number(Buf *b, double n)
{
    char text[64];
    int precision;

    if (!isfinite(n)) {
        /* JSON has no NaN and no infinity. Printing C's spelling of either would put a line on the
         * wire the factory cannot parse, losing the call altogether; null at least arrives. */
        buf_puts(b, "null");
        return;
    }
    /* The shortest form that reads back as the same double, so an echoed integer id still looks
     * like an integer rather than like 3.0000000000000000. */
    for (precision = 15; precision < 17; precision++) {
        snprintf(text, sizeof text, "%.*g", precision, n);
        if (strtod(text, NULL) == n) {
            buf_puts(b, text);
            return;
        }
    }
    snprintf(text, sizeof text, "%.17g", n);
    buf_puts(b, text);
}

static void write_string(Buf *b, const char *s)
{
    buf_putc(b, '"');
    for (; *s != '\0'; s++) {
        unsigned char c = (unsigned char)*s;

        switch (c) {
        case '"':  buf_puts(b, "\\\""); break;
        case '\\': buf_puts(b, "\\\\"); break;
        case '\n': buf_puts(b, "\\n");  break;
        case '\r': buf_puts(b, "\\r");  break;
        case '\t': buf_puts(b, "\\t");  break;
        case '\b': buf_puts(b, "\\b");  break;
        case '\f': buf_puts(b, "\\f");  break;
        default:
            if (c < 0x20) {
                char escape[8];
                snprintf(escape, sizeof escape, "\\u%04x", c);
                buf_puts(b, escape);
            } else {
                /* Anything else, including every byte of a multi-byte character, goes out as it
                 * came in; JSON is UTF-8 and needs no escaping above the control range. */
                buf_putc(b, (char)c);
            }
        }
    }
    buf_putc(b, '"');
}

static void json_write(Buf *b, const Json *node)
{
    size_t i;

    if (node == NULL) {
        buf_puts(b, "null");
        return;
    }
    switch (node->kind) {
    case JSON_NULL:
        buf_puts(b, "null");
        break;
    case JSON_BOOL:
        buf_puts(b, node->boolean ? "true" : "false");
        break;
    case JSON_NUMBER:
        write_number(b, node->number);
        break;
    case JSON_STRING:
        write_string(b, node->string);
        break;
    case JSON_ARRAY:
        buf_putc(b, '[');
        for (i = 0; i < node->count; i++) {
            if (i > 0) {
                buf_putc(b, ',');
            }
            json_write(b, node->items[i]);
        }
        buf_putc(b, ']');
        break;
    case JSON_OBJECT:
        buf_putc(b, '{');
        for (i = 0; i < node->count; i++) {
            if (i > 0) {
                buf_putc(b, ',');
            }
            write_string(b, node->keys[i]);
            buf_putc(b, ':');
            json_write(b, node->items[i]);
        }
        buf_putc(b, '}');
        break;
    }
}

static void write_id(Buf *b, const Json *id)
{
    buf_puts(b, "{\"id\":");
    json_write(b, id);
}

/* -> 0 if the reply could not be written, which is the factory having gone away or memory having
 * run out; either way there is nothing further this process can usefully do. */
static int emit(Buf *b)
{
    if (!b->ok) {
        return 0;
    }
    buf_putc(b, '\n');
    if (!b->ok) {
        return 0;
    }
    if (fwrite(b->data, 1, b->len, stdout) != b->len) {
        return 0;
    }
    return fflush(stdout) == 0;
}

static int reply_error(const Json *id, const char *message)
{
    Buf out;
    int written;

    buf_init(&out);
    write_id(&out, id);
    buf_puts(&out, ",\"ok\":false,\"error\":");
    write_string(&out, message != NULL ? message : "the subject refused without a message");
    buf_putc(&out, '}');
    written = emit(&out);
    buf_free(&out);
    return written;
}

/* One call. -> 0 if the reply could not be written. */
static int handle(const Json *request)
{
    const Json *id = json_get(request, "id");
    const Json *args = json_get(request, "args");
    const Json *op = json_get(request, "op");
    const Json *repeats_field = json_get(request, "repeats");
    Buf args_text;
    Buf out;
    int written;

    /* AN ARGS FIELD OF THE WRONG SHAPE IS A REFUSAL, NOT AN EMPTY CALL. This used to fall into the
     * `[]` default below, which is the most expensive kind of wrong: `{"args": "not-a-list"}` was
     * quietly rewritten into a call with no arguments, the subject dutifully answered 0, and the
     * reply said ok:true. A false SUCCESS enters grading as though it were a real answer, whereas
     * Go's version of this bug -- staying silent -- at least announced itself as a timeout. Python
     * and JavaScript both answer this line with a refusal.
     *
     * A MISSING args field keeps the `[]` default: the factory always sends the field, so its
     * absence is a hand-written line rather than a malformed call, and an empty argument list is a
     * reasonable reading of it. */
    if (args != NULL && args->kind != JSON_ARRAY) {
        return reply_error(id, "the arguments must be a JSON array");
    }
    buf_init(&args_text);
    if (args != NULL) {
        json_write(&args_text, args);
    } else {
        buf_puts(&args_text, "[]");
    }
    if (!args_text.ok) {
        buf_free(&args_text);
        return reply_error(id, "out of memory encoding the arguments");
    }

    if (op != NULL && op->kind == JSON_STRING && strcmp(op->string, "time") == 0) {
        /* TIMED HERE, on this side of the pipe. Measuring from the factory would charge the subject
         * for process startup and for JSON transport, which for a quick subject is most of the
         * clock, and a compiled subject is exactly the quick case. */
        long repeats = 1;
        long i;
        struct timespec started, finished;
        double elapsed;

        if (repeats_field != NULL && repeats_field->kind == JSON_NUMBER) {
            repeats = (long)repeats_field->number;
        }
        clock_gettime(CLOCK_MONOTONIC, &started);
        for (i = 0; i < repeats; i++) {
            const char *value;

            entry_error = NULL;
            value = entry(args_text.data);
            if (value == NULL) {
                buf_free(&args_text);
                return reply_error(id, entry_error);
            }
            free((void *)value);
        }
        clock_gettime(CLOCK_MONOTONIC, &finished);
        buf_free(&args_text);

        elapsed = (double)(finished.tv_sec - started.tv_sec)
                + (double)(finished.tv_nsec - started.tv_nsec) / 1e9;
        buf_init(&out);
        write_id(&out, id);
        buf_puts(&out, ",\"ok\":true,\"seconds\":");
        write_number(&out, elapsed);
        buf_putc(&out, '}');
        written = emit(&out);
        buf_free(&out);
        return written;
    }

    entry_error = NULL;
    {
        const char *value = entry(args_text.data);
        Json *parsed;

        buf_free(&args_text);
        if (value == NULL) {
            /* A REFUSAL IS AN ANSWER. How the subject rejects bad input is behaviour a
             * reimplementation has to reproduce, so it is reported and the loop reads on. */
            return reply_error(id, entry_error);
        }
        /* Re-encoded rather than spliced in as it stands: a subject that pretty-printed its answer
         * would otherwise put a newline in the middle of a reply and split one answer across two
         * lines, and a subject that returned something that is not JSON would corrupt the wire for
         * every call after it. */
        parsed = json_parse(value, strlen(value));
        free((void *)value);
        if (parsed == NULL) {
            return reply_error(id, "the subject returned text that is not JSON");
        }
        buf_init(&out);
        write_id(&out, id);
        buf_puts(&out, ",\"ok\":true,\"value\":");
        json_write(&out, parsed);
        buf_putc(&out, '}');
        json_free(parsed);
        written = emit(&out);
        buf_free(&out);
        return written;
    }
}

int main(void)
{
    char *line = NULL;
    size_t capacity = 0;
    ssize_t len;

    /* The factory closing the pipe first is not this process failing, but the default disposition
     * of SIGPIPE would make it look like one: the shim would die on a signal rather than reach the
     * end of main. Ignored here so the failed write comes back as an error instead. */
    signal(SIGPIPE, SIG_IGN);

    /* getline grows its own buffer to whatever the line needs, so a probe far larger than any read
     * the pipe happens to deliver is reassembled here rather than by hand. */
    while ((len = getline(&line, &capacity, stdin)) != -1) {
        Json *request;
        size_t length = (size_t)len;

        while (length > 0 && (line[length - 1] == '\n' || line[length - 1] == '\r'
                              || line[length - 1] == ' ' || line[length - 1] == '\t')) {
            length--;
        }
        if (length == 0) {
            continue;
        }
        request = json_parse(line, length);
        if (request == NULL) {
            continue;                               /* an unreadable line is not a call */
        }
        if (request->kind != JSON_OBJECT) {
            json_free(request);
            continue;
        }
        if (!handle(request)) {
            /* The factory closing the pipe first is not this process failing. */
            json_free(request);
            break;
        }
        json_free(request);
    }
    free(line);
    return 0;
}
