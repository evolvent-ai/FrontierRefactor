// --- frf: what a mined header's includer would have provided ---
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>
#include <algorithm>
using namespace std;
/*
	SubmissionId	:	36843200
	ContestId	:	952
	Index	:	C
	ProblemName	:	Ravioli Sort
	ProblemTags	:	['implementation']
	ProgrammingLanguage	:	GNU C++14
	Verdict	:	OK
*/

#include <bits/stdc++.h>

using namespace std;

vector <int> normalize(vector <int> v) {
	for (int i = 0; i < (int)v.size() - 1; i++)
		while (v[i] - v[i + 1] >= 2) {
			v[i]--;
			v[i + 1]++;
		}
	reverse(v.begin(), v.end());
	for (int i = 0; i < (int)v.size() - 1; i++)
		while (v[i] - v[i + 1] >= 2) {
			v[i]--;
			v[i + 1]++;
		}
	reverse(v.begin(), v.end());
	return v;
}

vector <int> removeZeros(vector <int> v) {
	vector <int> ret;
	for (int i = 0; i < v.size(); i++)
		if (v[i] > 0)
			ret.push_back(v[i]);
	return ret;
}

vector <int> removeMax(vector <int> v) {
	vector <int> ret;
	int idx = 0;
	for (int i = 0; i < v.size(); i++)
		if (v[i] > v[idx])
			idx = i;
	for (int i = 0; i < v.size(); i++)
		if (i != idx)
			ret.push_back(v[i]);
	return ret;
}

int frfUnusedMain() {
	int n;
	vector <int> v, v2;
	cin >> n;
	for (int i = 0; i < n; i++) {
		int x;
		cin >> x;
		v.push_back(x);
	}
	vector <int> sorted = v;
	vector <int> reversed = v;
	sort(sorted.begin(), sorted.end());
	sort(reversed.begin(), reversed.end());
	reverse(reversed.begin(), reversed.end());
	for (int i = 1; i <= n; i++) {
		v = normalize(v);
		int mx = *max_element(v.begin(), v.end());
		v2.push_back(mx);
		v2 = normalize(v2);
		v = removeMax(v);
	}
	if (v2 == sorted || v2 == reversed)
		cout << "YES" << endl;
	else
		cout << "NO" << endl;
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
    if (frf_items.size() != 1) return frf_refuse("wrong number of arguments");
    if (frf_items[0].kind != frf::Value::Array) return frf_refuse("argument 0 is not an array");
    std::vector<int> frf_arg0;
    for (const frf::Value &frf_item : frf_items[0].items) {
        long long frf_scalar = 0;
        if (!frf::as_int(frf_item, frf_scalar)) return frf_refuse("argument 0 has a non-integer element");
        frf_arg0.push_back(static_cast<int>(frf_scalar));
    }
    auto frf_value = normalize(frf_arg0);
    std::string frf_out = "[";
    for (std::size_t frf_i = 0; frf_i < frf_value.size(); frf_i++) {
        if (frf_i) frf_out.push_back(',');
        frf_out += frf::number_text(static_cast<double>(frf_value[frf_i]));
    }
    frf_out.push_back(']');
    return frf::own(frf_out);
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