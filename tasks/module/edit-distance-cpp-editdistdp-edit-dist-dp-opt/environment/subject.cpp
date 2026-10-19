// --- frf: what a mined header's includer would have provided ---
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>
#include <algorithm>
using namespace std;
/* Given two strings str1 & str2
 * and below operations that can
 * be performed on str1. Find
 * minimum number of edits
 * (operations) required to convert
 * 'str1' into 'str2'/
 * a. Insert
 * b. Remove
 * c. Replace
 * All of the above operations are
 * of equal cost
 */

#include <iostream>
#include <string>
#include <vector>
using namespace std;

int min(int x, int y, int z) { return min(min(x, y), z); }

/* A Naive recursive C++ program to find
 * minimum number of operations to convert
 * str1 to str2.
 * O(3^m)
 */
int editDist(string str1, string str2, int m, int n) {
    if (m == 0)
        return n;
    if (n == 0)
        return m;

    // If last characters are same then continue
    // for the rest of them.
    if (str1[m - 1] == str2[n - 1])
        return editDist(str1, str2, m - 1, n - 1);

    // If last not same, then 3 possibilities
    // a.Insert b.Remove c. Replace
    // Get min of three and continue for rest.
    return 1 + min(editDist(str1, str2, m, n - 1),
                   editDist(str1, str2, m - 1, n),
                   editDist(str1, str2, m - 1, n - 1));
}

/* A DP based program
 * O(m x n)
 */
int editDistDP(string str1, string str2, int m, int n) {
    // Create Table for SubProblems
    std::vector<std::vector<int> > dp(m + 1, std::vector<int>(n + 1));

    // Fill d[][] in bottom up manner
    for (int i = 0; i <= m; i++) {
        for (int j = 0; j <= n; j++) {
            // If str1 empty. Then add all of str2
            if (i == 0)
                dp[i][j] = j;

            // If str2 empty. Then add all of str1
            else if (j == 0)
                dp[i][j] = i;

            // If character same. Recur for remaining
            else if (str1[i - 1] == str2[j - 1])
                dp[i][j] = dp[i - 1][j - 1];

            else
                dp[i][j] = 1 + min(dp[i][j - 1],     // Insert
                                   dp[i - 1][j],     // Remove
                                   dp[i - 1][j - 1]  // Replace
                               );
        }
    }

    return dp[m][n];
}

int frfUnusedMain() {
    string str1 = "sunday";
    string str2 = "saturday";

    cout << editDist(str1, str2, str1.length(), str2.length()) << endl;
    cout << editDistDP(str1, str2, str1.length(), str2.length()) << endl;

    return 0;
}

// --- frf call bridge (generated) ---
#include <cstdlib>
#include <cstring>
#include <exception>
#include <string>
#include <vector>

extern "C" { char *entry_error = nullptr; }

namespace frf {

// A JSON value, only as far as this wire carries one. Deliberately not a general parser: it reads the
// argument array serve.c hands over, and nothing else ever reaches it.
struct Value {
    enum Kind { Null, Bool, Number, String, Array } kind = Null;
    bool boolean = false;
    double number = 0.0;
    std::string text;
    std::vector<Value> items;
};

inline void skip(const char *&at) {
    while (*at == ' ' || *at == '\t' || *at == '\n' || *at == '\r') at++;
}

bool parse(const char *&at, Value &out);

inline bool parse_string(const char *&at, std::string &out) {
    if (*at != '"') return false;
    at++;
    while (*at && *at != '"') {
        if (*at == '\\') {
            at++;
            switch (*at) {
                case 'n': out.push_back('\n'); break;
                case 't': out.push_back('\t'); break;
                case 'r': out.push_back('\r'); break;
                case 'b': out.push_back('\b'); break;
                case 'f': out.push_back('\f'); break;
                // A \uXXXX escape is carried as the bytes that spell it rather than decoded: this
                // side only ever hands the string back to the subject, and a half-decoded surrogate
                // pair would be a different string from the one the factory sent.
                case 'u': out.append("\\u"); for (int i = 0; i < 4 && at[1]; i++) out.push_back(*++at); break;
                case '\0': return false;
                default: out.push_back(*at);
            }
            at++;
            continue;
        }
        out.push_back(*at++);
    }
    if (*at != '"') return false;
    at++;
    return true;
}

inline bool parse(const char *&at, Value &out) {
    skip(at);
    if (*at == 'n' && std::strncmp(at, "null", 4) == 0) { at += 4; out.kind = Value::Null; return true; }
    if (*at == 't' && std::strncmp(at, "true", 4) == 0) {
        at += 4; out.kind = Value::Bool; out.boolean = true; return true;
    }
    if (*at == 'f' && std::strncmp(at, "false", 5) == 0) {
        at += 5; out.kind = Value::Bool; out.boolean = false; return true;
    }
    if (*at == '"') { out.kind = Value::String; return parse_string(at, out.text); }
    if (*at == '[') {
        at++;
        out.kind = Value::Array;
        skip(at);
        if (*at == ']') { at++; return true; }
        for (;;) {
            Value item;
            if (!parse(at, item)) return false;
            out.items.push_back(item);
            skip(at);
            if (*at == ',') { at++; continue; }
            if (*at == ']') { at++; return true; }
            return false;
        }
    }
    if (*at == '{') {
        // An object is not something any parameter of this wire is drawn as, so it is READ AND
        // REFUSED rather than skipped: silently accepting one would call the subject with a
        // default-constructed value and charge the answer to it.
        return false;
    }
    {
        char *end = nullptr;
        double number = std::strtod(at, &end);
        if (end == at) return false;
        at = end;
        out.kind = Value::Number;
        out.number = number;
        return true;
    }
}

// A malloc'd copy, because serve.c frees what entry returns.
inline const char *own(const std::string &text) {
    char *out = static_cast<char *>(std::malloc(text.size() + 1));
    if (out == nullptr) return nullptr;
    std::memcpy(out, text.c_str(), text.size() + 1);
    return out;
}

inline std::string number_text(double value) {
    // %.17g round-trips a double exactly, and an integral value is written without a fractional part
    // so that an integer answer is frozen as an integer.
    char buffer[40];
    if (value == static_cast<double>(static_cast<long long>(value))) {
        std::snprintf(buffer, sizeof buffer, "%lld", static_cast<long long>(value));
    } else {
        std::snprintf(buffer, sizeof buffer, "%.17g", value);
    }
    return std::string(buffer);
}

inline bool as_int(const Value &value, long long &out) {
    if (value.kind != Value::Number) return false;
    if (value.number != static_cast<double>(static_cast<long long>(value.number))) return false;
    out = static_cast<long long>(value.number);
    return true;
}

}  // namespace frf

// The message entry_error points at. Static storage: serve.c reads it and never frees it.
static std::string frf_message;

static const char *frf_refuse(const char *why) {
    frf_message = why;
    entry_error = const_cast<char *>(frf_message.c_str());
    return nullptr;
}

// The work; `entry` below wraps it so a thrown exception cannot cross into serve.c.
static const char *frf_call(const char *args_json) {
    const char *frf_at = args_json;
    frf::Value frf_parsed;
    if (!frf::parse(frf_at, frf_parsed) || frf_parsed.kind != frf::Value::Array) return frf_refuse("the arguments must be a JSON array");
    const std::vector<frf::Value> &frf_items = frf_parsed.items;
    if (frf_items.size() != 4) return frf_refuse("wrong number of arguments");
    if (frf_items[0].kind != frf::Value::String) return frf_refuse("argument 0 is not a string");
    std::string frf_arg0 = frf_items[0].text;
    if (frf_items[1].kind != frf::Value::String) return frf_refuse("argument 1 is not a string");
    std::string frf_arg1 = frf_items[1].text;
    long long frf_arg2 = 0;
    if (!frf::as_int(frf_items[2], frf_arg2)) return frf_refuse("argument 2 is not an integer");
    long long frf_arg3 = 0;
    if (!frf::as_int(frf_items[3], frf_arg3)) return frf_refuse("argument 3 is not an integer");
    auto frf_value = editDistDP(frf_arg0, frf_arg1, frf_arg2, frf_arg3);
    return frf::own(frf::number_text(static_cast<double>(frf_value)));
}

// entry is what serve.c calls. See frf/observe/call/bridge.py.
extern "C" const char *entry(const char *args_json) {
    // A THROWN EXCEPTION CANNOT CROSS THIS BOUNDARY, and serve.c has no way to catch one:
    // it is compiled as C. An exception escaping here terminates the process, so every probe
    // queued behind it is lost -- the same fault that cost the Rust shim 47% to 100% of a
    // corpus before it caught unwinds. std::out_of_range from .at(), std::bad_alloc, a
    // std::domain_error: all of them are ways real C++ refuses, and a refusal is an ANSWER.
    try {
        return frf_call(args_json);
    } catch (const std::exception &failure) {
        return frf_refuse(failure.what());
    } catch (...) {
        // A thrown int, a thrown string, a custom type: no message to report, but still an
        // answer rather than a dead process.
        return frf_refuse("the subject threw a non-standard exception");
    }
}