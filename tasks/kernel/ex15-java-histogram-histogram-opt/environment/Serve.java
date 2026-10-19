// Serve a Java subject over the wire. Written into the task; not imported by the factory.
//
// The subject supplies a class `Subject` with
//
//     public static Object entry(java.util.List<Object> args)
//
// answering with a value or throwing to refuse. It is called through reflection rather than named
// directly, so that a subject which failed to compile, or compiled under another name, produces a
// sentence on stderr instead of a linkage error out of the class loader.
//
// The JSON reader and writer at the bottom of the file are here because the standard library has no
// JSON and these run in an offline container where a dependency cannot be fetched. They are a real
// recursive-descent parser and a real serialiser: a subject's arguments include nested arrays and
// strings with escapes in them, and anything built out of splitting on commas would mangle those
// quietly, which is the worst way for a harness to be wrong.
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.lang.reflect.Array;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

public final class Serve {

    public static void main(String[] arguments) {
        Method entry;
        try {
            entry = resolveEntry();
        } catch (ReflectiveOperationException absent) {
            // A missing entry point is NOT a refusal. Answering ok:false to every call would present
            // a broken build as a subject that rejects everything, and the factory keeps those two
            // findings apart on purpose: one is a wrong submission, the other is a wrong environment.
            // Exiting is what lets it tell them apart.
            System.err.println("serve: " + describe(absent));
            System.exit(1);
            return;
        }

        // The streams are wrapped with an explicit charset rather than left to the platform default,
        // because the default varies by machine and the wire has to read the same everywhere.
        BufferedReader in = new BufferedReader(
                new InputStreamReader(System.in, StandardCharsets.UTF_8));
        Writer out = new BufferedWriter(
                new OutputStreamWriter(System.out, StandardCharsets.UTF_8));
        try {
            String line;
            while ((line = in.readLine()) != null) {
                Object parsed;
                try {
                    parsed = new JsonReader(line).read();
                } catch (JsonException unreadable) {
                    continue;                         // an unreadable line is not a call
                }
                if (!(parsed instanceof Map)) {
                    continue;
                }
                write(out, serve(asObject(parsed), entry));
            }
        } catch (IOException broken) {
            // stdout carries answers and nothing else, so stderr is the only place this can be said.
            System.err.println("serve: reading stdin: " + describe(broken));
            System.exit(1);
        }
        // End of input is the factory closing the pipe, which is an ordinary shutdown.
    }

    private static Method resolveEntry() throws ReflectiveOperationException {
        return Class.forName("Subject").getMethod("entry", List.class);
    }

    /** Answer one request. */
    private static Map<String, Object> serve(Map<String, Object> request, Method entry) {
        // The id is echoed back exactly as it arrived. Read into a long and written out again it
        // would be this shim's idea of the number rather than the caller's.
        Object id = request.get("id");
        Object op = request.get("op");
        Object rawArgs = request.get("args");
        // AN ARGS FIELD OF THE WRONG SHAPE IS A REFUSAL, NOT AN EMPTY CALL. Collapsing both into an
        // empty list is the most expensive kind of wrong: {"args": "not-a-list"} was quietly
        // rewritten into a call with no arguments, the subject answered whatever a no-argument call
        // returns, and the reply said ok:true. A false SUCCESS enters grading as though it were a
        // real answer.
        //
        // A MISSING field keeps the empty default: the factory always sends "args", so its absence is
        // a hand-written line rather than a malformed call.
        if (rawArgs != null && !(rawArgs instanceof List)) {
            return reply(id, false, "error", "the arguments must be a JSON array");
        }
        List<Object> args = (rawArgs instanceof List) ? asArray(rawArgs) : new ArrayList<Object>();
        // `call` names the entry point. A single-function subject has exactly one, so it is read and
        // ignored; the field exists for a subject that later has more than one.

        if ("time".equals(op)) {
            Object rawRepeats = request.get("repeats");
            int repeats = (rawRepeats instanceof Number) ? ((Number) rawRepeats).intValue() : 1;
            if (repeats < 1) {
                // Absent on a run request, and timing no calls at all would report zero seconds,
                // which reads as an infinitely fast subject rather than as a malformed request.
                repeats = 1;
            }
            // TIMED HERE, on this side of the pipe. Measured from the factory the subject would be
            // charged for JVM startup and for JSON transport, and on a subject whose real work takes
            // a millisecond that overhead is most of what the clock would see. nanoTime rather than
            // currentTimeMillis because only the former is monotonic and has the resolution for it.
            long started = System.nanoTime();
            for (int i = 0; i < repeats; i++) {
                Outcome outcome = attempt(entry, args);
                if (outcome.failure != null) {
                    return reply(id, false, "error", outcome.failure);
                }
            }
            double seconds = (System.nanoTime() - started) / 1_000_000_000.0;
            return reply(id, true, "seconds", Double.valueOf(seconds));
        }

        Outcome outcome = attempt(entry, args);
        if (outcome.failure != null) {
            // A REFUSAL IS AN ANSWER. How the subject rejects bad input is behaviour a
            // reimplementation has to reproduce, so it is reported and the next line is read.
            return reply(id, false, "error", outcome.failure);
        }
        return reply(id, true, "value", outcome.value);
    }

    /** What one call produced: a value, or the description of a refusal. */
    private static final class Outcome {
        final Object value;
        final String failure;                         // null when the call returned

        Outcome(Object value, String failure) {
            this.value = value;
            this.failure = failure;
        }
    }

    private static Outcome attempt(Method entry, List<Object> args) {
        try {
            // The argument array is spelled out rather than left to varargs, which would otherwise
            // have to guess whether a List is the single parameter or the parameter list itself.
            return new Outcome(entry.invoke(null, new Object[] {args}), null);
        } catch (InvocationTargetException refused) {
            // The throwable the subject actually raised is the cause. Reporting the wrapper would
            // describe this shim's use of reflection instead of the subject's behaviour.
            Throwable cause = refused.getCause();
            return new Outcome(null, describe(cause != null ? cause : refused));
        } catch (Throwable failure) {
            // Throwable and not Exception, because an Error is one of the ways Java code refuses --
            // a StackOverflowError out of a recursion, an AssertionError out of a check -- and it
            // has to arrive as an answer rather than take the process down with the rest of the
            // corpus behind it.
            return new Outcome(null, describe(failure));
        }
    }

    /**
     * Render a refusal as "TypeName: message", and never as a stack trace.
     *
     * A trace carries the absolute paths of the machine that produced it; frozen into an expectation
     * those could not be reproduced anywhere else. The message is dropped when it is absent rather
     * than printed as the word "null", which would read as part of what the subject said.
     */
    private static String describe(Throwable failure) {
        String name = failure.getClass().getName();
        String message = failure.getMessage();
        return (message == null || message.isEmpty()) ? name : name + ": " + message;
    }

    private static Map<String, Object> reply(Object id, boolean ok, String field, Object payload) {
        Map<String, Object> body = new LinkedHashMap<String, Object>();
        body.put("id", id);
        body.put("ok", Boolean.valueOf(ok));
        body.put(field, payload);
        return body;
    }

    /** Put one reply on stdout, as one line, flushed. */
    private static void write(Writer out, Map<String, Object> reply) throws IOException {
        // Serialised into a buffer first: a value that turns out to be unencodable halfway through
        // would otherwise already have put half a line on the wire, and half a line cannot be read
        // as anything.
        StringBuilder body = new StringBuilder();
        try {
            writeValue(reply, body);
        } catch (JsonException unencodable) {
            // The subject answered with something JSON cannot carry. That is an answer which failed
            // to encode rather than a broken wire, so it is reported as a refusal; writing nothing
            // would leave the factory waiting on a line that never comes.
            body.setLength(0);
            try {
                writeValue(reply(reply.get("id"), false, "error",
                                 "the returned value could not be encoded as JSON: "
                                         + unencodable.getMessage()),
                           body);
            } catch (JsonException idUnencodable) {
                // Even the id would not encode, which a value off the wire can manage: "1e999" is
                // valid JSON and reads as an infinity, which has no spelling to write back. A line
                // without a usable id is a poor answer but it is still an answer, and the factory
                // records an unmatched reply rather than blocking on one that never arrives.
                body.setLength(0);
                body.append("{\"ok\":false,\"error\":\"the reply could not be encoded as JSON\"}");
            }
        }
        out.write(body.toString());
        out.write('\n');
        out.flush();
    }

    private static void writeValue(Object value, StringBuilder out) {
        if (value == null) {
            out.append("null");
        } else if (value instanceof String) {
            writeString((String) value, out);
        } else if (value instanceof Character) {
            writeString(value.toString(), out);
        } else if (value instanceof Boolean) {
            out.append(((Boolean) value).booleanValue() ? "true" : "false");
        } else if (value instanceof Double || value instanceof Float) {
            double number = ((Number) value).doubleValue();
            if (Double.isNaN(number) || Double.isInfinite(number)) {
                // JSON has no spelling for these, and inventing one (a bare NaN, a quoted string)
                // would produce a line the far side reads as a different answer than the one meant.
                throw new JsonException("JSON cannot carry " + number);
            }
            out.append(Double.toString(number));
        } else if (value instanceof Number) {
            out.append(value.toString());
        } else if (value instanceof Map) {
            writeObject((Map<?, ?>) value, out);
        } else if (value instanceof Iterable) {
            writeIterable((Iterable<?>) value, out);
        } else if (value.getClass().isArray()) {
            // Reflection over the array covers int[], double[] and Object[] alike, which is worth
            // it because returning an array is the ordinary way for Java to answer with a sequence.
            int length = Array.getLength(value);
            out.append('[');
            for (int i = 0; i < length; i++) {
                if (i > 0) {
                    out.append(',');
                }
                writeValue(Array.get(value, i), out);
            }
            out.append(']');
        } else {
            // Deliberately not toString(). The default one prints an identity hash, which differs
            // between runs of the same program, so a subject answering with a plain object would
            // freeze an expectation nothing could ever reproduce -- including itself.
            throw new JsonException("a value of type " + value.getClass().getName()
                    + " cannot be carried on the wire");
        }
    }

    private static void writeObject(Map<?, ?> value, StringBuilder out) {
        out.append('{');
        boolean first = true;
        for (Map.Entry<?, ?> field : value.entrySet()) {
            if (!first) {
                out.append(',');
            }
            first = false;
            writeString(String.valueOf(field.getKey()), out);
            out.append(':');
            writeValue(field.getValue(), out);
        }
        out.append('}');
    }

    private static void writeIterable(Iterable<?> value, StringBuilder out) {
        out.append('[');
        boolean first = true;
        for (Object item : value) {
            if (!first) {
                out.append(',');
            }
            first = false;
            writeValue(item, out);
        }
        out.append(']');
    }

    private static void writeString(String value, StringBuilder out) {
        out.append('"');
        for (int i = 0; i < value.length(); i++) {
            char c = value.charAt(i);
            switch (c) {
                case '"':  out.append("\\\""); break;
                case '\\': out.append("\\\\"); break;
                case '\b': out.append("\\b"); break;
                case '\f': out.append("\\f"); break;
                case '\n': out.append("\\n"); break;
                case '\r': out.append("\\r"); break;
                case '\t': out.append("\\t"); break;
                default:
                    if (c < 0x20 || c > 0x7e) {
                        // Everything outside printable ASCII is escaped, so the reply is the same
                        // bytes whatever encoding the far end assumes. Locale.ROOT because a few
                        // locales format digits with their own numerals, and the same value must
                        // serialise identically on every machine.
                        out.append(String.format(Locale.ROOT, "\\u%04x", Integer.valueOf(c)));
                    } else {
                        out.append(c);
                    }
                    break;
            }
        }
        out.append('"');
    }

    /** A line that is not JSON, or a value that is not JSON. Unchecked: both are handled locally. */
    private static final class JsonException extends RuntimeException {
        private static final long serialVersionUID = 1L;

        JsonException(String message) {
            super(message);
        }
    }

    /**
     * A recursive-descent reader for one line of JSON.
     *
     * Objects arrive as LinkedHashMap and arrays as ArrayList; a number with no fraction and no
     * exponent arrives as Long and any other as Double, because an argument list of array indices
     * read as floating point would be handed to the subject as something it never received.
     */
    /* How deeply a request may nest. A line from the wire is nested only as deeply as the
     * arguments are, and a limit keeps a pathological line from exhausting the stack of this
     * recursive-descent parser. Without it a deeply nested line raises StackOverflowError out of
     * the reader, which is not caught as a refusal is -- the process dies and the rest of the
     * corpus is lost. The C and Rust shims cap depth for exactly this reason; this one did not,
     * and that asymmetry was the bug. */
    private static final int MAX_DEPTH = 200;

    private static final class JsonReader {
        private final String text;
        private int at;
        private int depth;

        JsonReader(String text) {
            this.text = text;
        }

        Object read() {
            skipSpace();
            Object value = readValue();
            skipSpace();
            if (at != text.length()) {
                throw new JsonException("trailing text after the value");
            }
            return value;
        }

        private Object readValue() {
            char c = peek();
            switch (c) {
                case '{': return readContainer(true);
                case '[': return readContainer(false);
                case '"': return readString();
                case 't': expect("true"); return Boolean.TRUE;
                case 'f': expect("false"); return Boolean.FALSE;
                case 'n': expect("null"); return null;
                default:
                    if (c == '-' || (c >= '0' && c <= '9')) {
                        return readNumber();
                    }
                    throw new JsonException("unexpected character " + c);
            }
        }

        /* The one place recursion deepens, so the one place the limit has to be enforced. Both
         * containers funnel through here rather than each counting for itself, which is how the
         * two would otherwise drift apart. */
        private Object readContainer(boolean isObject) {
            if (++depth > MAX_DEPTH) {
                throw new JsonException("nested more than " + MAX_DEPTH + " deep");
            }
            try {
                return isObject ? readObject() : readArray();
            } finally {
                depth--;
            }
        }

        private Map<String, Object> readObject() {
            at++;
            Map<String, Object> members = new LinkedHashMap<String, Object>();
            skipSpace();
            if (peek() == '}') {
                at++;
                return members;
            }
            while (true) {
                skipSpace();
                String name = readString();
                skipSpace();
                if (next() != ':') {
                    throw new JsonException("expected a colon after a field name");
                }
                skipSpace();
                members.put(name, readValue());
                skipSpace();
                char c = next();
                if (c == '}') {
                    return members;
                }
                if (c != ',') {
                    throw new JsonException("expected a comma or a closing brace");
                }
            }
        }

        private List<Object> readArray() {
            at++;
            List<Object> items = new ArrayList<Object>();
            skipSpace();
            if (peek() == ']') {
                at++;
                return items;
            }
            while (true) {
                skipSpace();
                items.add(readValue());
                skipSpace();
                char c = next();
                if (c == ']') {
                    return items;
                }
                if (c != ',') {
                    throw new JsonException("expected a comma or a closing bracket");
                }
            }
        }

        private String readString() {
            if (next() != '"') {
                throw new JsonException("expected a string");
            }
            StringBuilder value = new StringBuilder();
            while (true) {
                char c = next();
                if (c == '"') {
                    return value.toString();
                }
                if (c != '\\') {
                    if (c < 0x20) {
                        throw new JsonException("an unescaped control character in a string");
                    }
                    value.append(c);
                    continue;
                }
                char escape = next();
                switch (escape) {
                    case '"':  value.append('"');  break;
                    case '\\': value.append('\\'); break;
                    case '/':  value.append('/');  break;
                    case 'b':  value.append('\b'); break;
                    case 'f':  value.append('\f'); break;
                    case 'n':  value.append('\n'); break;
                    case 'r':  value.append('\r'); break;
                    case 't':  value.append('\t'); break;
                    // A code point above the basic plane arrives as two of these in a row. Appending
                    // each unit as it comes reassembles the surrogate pair, which is exactly how
                    // Java holds such a character anyway, so no special case is needed for it.
                    case 'u':  value.append(readFourHexDigits()); break;
                    default: throw new JsonException("unknown escape \\" + escape);
                }
            }
        }

        private char readFourHexDigits() {
            if (at + 4 > text.length()) {
                throw new JsonException("a truncated \\u escape");
            }
            int code = 0;
            for (int i = 0; i < 4; i++) {
                int digit = Character.digit(text.charAt(at + i), 16);
                if (digit < 0) {
                    throw new JsonException("a malformed \\u escape");
                }
                code = code * 16 + digit;
            }
            at += 4;
            return (char) code;
        }

        private Object readNumber() {
            int start = at;
            if (peek() == '-') {
                at++;
            }
            readDigits();
            boolean integral = true;
            if (at < text.length() && text.charAt(at) == '.') {
                integral = false;
                at++;
                readDigits();
            }
            if (at < text.length() && (text.charAt(at) == 'e' || text.charAt(at) == 'E')) {
                integral = false;
                at++;
                if (at < text.length() && (text.charAt(at) == '+' || text.charAt(at) == '-')) {
                    at++;
                }
                readDigits();
            }
            String token = text.substring(start, at);
            if (integral) {
                try {
                    return Long.valueOf(token);
                } catch (NumberFormatException tooBig) {
                    // An integer past 64 bits is still a number the far side sent, so it is carried
                    // approximately rather than rejected as an unreadable line.
                    return Double.valueOf(token);
                }
            }
            return Double.valueOf(token);
        }

        private void readDigits() {
            int start = at;
            while (at < text.length() && text.charAt(at) >= '0' && text.charAt(at) <= '9') {
                at++;
            }
            if (at == start) {
                throw new JsonException("expected a digit");
            }
        }

        private void skipSpace() {
            while (at < text.length()) {
                char c = text.charAt(at);
                if (c == ' ' || c == '\t' || c == '\n' || c == '\r') {
                    at++;
                } else {
                    break;
                }
            }
        }

        private void expect(String literal) {
            if (!text.startsWith(literal, at)) {
                throw new JsonException("expected " + literal);
            }
            at += literal.length();
        }

        private char peek() {
            if (at >= text.length()) {
                throw new JsonException("the line ended in the middle of a value");
            }
            return text.charAt(at);
        }

        private char next() {
            char c = peek();
            at++;
            return c;
        }
    }

    @SuppressWarnings("unchecked")
    private static Map<String, Object> asObject(Object value) {
        return (Map<String, Object>) value;
    }

    @SuppressWarnings("unchecked")
    private static List<Object> asArray(Object value) {
        return (List<Object>) value;
    }

    private Serve() {
    }
}
