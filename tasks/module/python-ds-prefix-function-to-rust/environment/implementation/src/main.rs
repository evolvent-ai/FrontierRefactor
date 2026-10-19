//! Serve a Rust subject over the wire. Written into the task; not required by the factory.
//!
//! The subject supplies, in `subject.rs` beside this file:
//!
//! ```ignore
//! pub fn entry(args: &crate::Json) -> Result<crate::Json, String>
//! ```
//!
//! where `args` is always `Json::Array`, and `Err(message)` is how it refuses. A refusal is an
//! answer, so it is reported as `{"ok":false,"error":message}` and the loop carries on reading.
//! Rust has no exception type to name, so the message the subject chose is the whole of the error
//! text; the other shims prefix a type name because their languages have one.
//!
//! WHY THERE IS A JSON PARSER IN HERE. The standard library has no JSON and these tasks run in an
//! offline container with no crates available, so the wire's own codec has to be part of the shim.
//! It is a real parser over the grammar rather than a string split, because the arguments it has to
//! read include strings containing braces, commas and escaped quotes.

// The codec exposes rather more of `Json` than any single subject will call, and a subject that
// never asks for, say, `as_str` should not make the build noisy.
#![allow(dead_code)]

mod subject;

use std::fmt::Write as _;
use std::io::{self, BufRead, Write};
use std::panic::{self, AssertUnwindSafe};
use std::time::Instant;

/// One JSON value.
///
/// Objects keep their pairs in a `Vec` rather than a map so that a value read from the wire and
/// written back out preserves its key order, and so that reading needs no allocation per lookup.
#[derive(Debug, Clone, PartialEq)]
pub enum Json {
    Null,
    Bool(bool),
    Number(f64),
    String(String),
    Array(Vec<Json>),
    Object(Vec<(String, Json)>),
}

impl Json {
    /// The value of `key`, for an object; `None` for anything else, so a caller need not first
    /// check that the request was an object at all.
    pub fn get(&self, key: &str) -> Option<&Json> {
        match self {
            Json::Object(pairs) => pairs.iter().find(|(k, _)| k == key).map(|(_, v)| v),
            _ => None,
        }
    }

    pub fn as_array(&self) -> Option<&[Json]> {
        match self {
            Json::Array(items) => Some(items),
            _ => None,
        }
    }

    pub fn as_f64(&self) -> Option<f64> {
        match self {
            Json::Number(n) => Some(*n),
            _ => None,
        }
    }

    pub fn as_str(&self) -> Option<&str> {
        match self {
            Json::String(s) => Some(s),
            _ => None,
        }
    }
}

// A line arriving from the wire is nested only as deeply as the arguments are, and a limit keeps a
// pathological line from exhausting the stack in a recursive-descent parser.
const MAX_DEPTH: usize = 200;

struct Parser<'a> {
    bytes: &'a [u8],
    pos: usize,
}

impl<'a> Parser<'a> {
    fn peek(&self) -> Option<u8> {
        self.bytes.get(self.pos).copied()
    }

    fn bump(&mut self) -> Option<u8> {
        let b = self.peek();
        if b.is_some() {
            self.pos += 1;
        }
        b
    }

    fn skip_space(&mut self) {
        while matches!(self.peek(), Some(b' ' | b'\t' | b'\n' | b'\r')) {
            self.pos += 1;
        }
    }

    fn expect(&mut self, byte: u8) -> Result<(), String> {
        if self.bump() == Some(byte) {
            Ok(())
        } else {
            Err(format!("expected {:?} at byte {}", byte as char, self.pos))
        }
    }

    fn literal(&mut self, word: &str) -> Result<(), String> {
        if self.bytes[self.pos..].starts_with(word.as_bytes()) {
            self.pos += word.len();
            Ok(())
        } else {
            Err(format!("expected {} at byte {}", word, self.pos))
        }
    }

    fn value(&mut self, depth: usize) -> Result<Json, String> {
        if depth > MAX_DEPTH {
            return Err("nesting too deep".to_string());
        }
        self.skip_space();
        match self.peek() {
            None => Err("unexpected end of input".to_string()),
            Some(b'n') => self.literal("null").map(|()| Json::Null),
            Some(b't') => self.literal("true").map(|()| Json::Bool(true)),
            Some(b'f') => self.literal("false").map(|()| Json::Bool(false)),
            Some(b'"') => self.string().map(Json::String),
            Some(b'[') => self.array(depth),
            Some(b'{') => self.object(depth),
            Some(b'-' | b'0'..=b'9') => self.number(),
            Some(b) => Err(format!("unexpected {:?} at byte {}", b as char, self.pos)),
        }
    }

    fn array(&mut self, depth: usize) -> Result<Json, String> {
        self.expect(b'[')?;
        let mut items = Vec::new();
        self.skip_space();
        if self.peek() == Some(b']') {
            self.pos += 1;
            return Ok(Json::Array(items));
        }
        loop {
            items.push(self.value(depth + 1)?);
            self.skip_space();
            match self.bump() {
                Some(b',') => continue,
                Some(b']') => return Ok(Json::Array(items)),
                _ => return Err(format!("expected ',' or ']' at byte {}", self.pos)),
            }
        }
    }

    fn object(&mut self, depth: usize) -> Result<Json, String> {
        self.expect(b'{')?;
        let mut pairs = Vec::new();
        self.skip_space();
        if self.peek() == Some(b'}') {
            self.pos += 1;
            return Ok(Json::Object(pairs));
        }
        loop {
            self.skip_space();
            let key = self.string()?;
            self.skip_space();
            self.expect(b':')?;
            let value = self.value(depth + 1)?;
            pairs.push((key, value));
            self.skip_space();
            match self.bump() {
                Some(b',') => continue,
                Some(b'}') => return Ok(Json::Object(pairs)),
                _ => return Err(format!("expected ',' or '}}' at byte {}", self.pos)),
            }
        }
    }

    fn number(&mut self) -> Result<Json, String> {
        let start = self.pos;
        if self.peek() == Some(b'-') {
            self.pos += 1;
        }
        while matches!(self.peek(), Some(b'0'..=b'9')) {
            self.pos += 1;
        }
        if self.peek() == Some(b'.') {
            self.pos += 1;
            while matches!(self.peek(), Some(b'0'..=b'9')) {
                self.pos += 1;
            }
        }
        if matches!(self.peek(), Some(b'e' | b'E')) {
            self.pos += 1;
            if matches!(self.peek(), Some(b'+' | b'-')) {
                self.pos += 1;
            }
            while matches!(self.peek(), Some(b'0'..=b'9')) {
                self.pos += 1;
            }
        }
        let text = std::str::from_utf8(&self.bytes[start..self.pos])
            .map_err(|_| "number was not text".to_string())?;
        text.parse::<f64>()
            .map(Json::Number)
            .map_err(|_| format!("bad number {:?}", text))
    }

    fn string(&mut self) -> Result<String, String> {
        self.expect(b'"')?;
        let mut out = String::new();
        loop {
            match self.bump() {
                None => return Err("unterminated string".to_string()),
                Some(b'"') => return Ok(out),
                Some(b'\\') => self.escape(&mut out)?,
                Some(b) if b < 0x20 => {
                    return Err(format!("raw control byte {:#04x} in string", b))
                }
                Some(b) => {
                    // Anything else is passed through as the bytes it already was, so multi-byte
                    // UTF-8 needs no special case; the whole line was validated as UTF-8 on the
                    // way in.
                    let start = self.pos - 1;
                    while matches!(self.peek(), Some(c) if c >= 0x80) {
                        self.pos += 1;
                    }
                    if b < 0x80 {
                        out.push(b as char);
                    } else {
                        out.push_str(
                            std::str::from_utf8(&self.bytes[start..self.pos])
                                .map_err(|_| "invalid UTF-8 in string".to_string())?,
                        );
                    }
                }
            }
        }
    }

    fn escape(&mut self, out: &mut String) -> Result<(), String> {
        match self.bump() {
            Some(b'"') => out.push('"'),
            Some(b'\\') => out.push('\\'),
            Some(b'/') => out.push('/'),
            Some(b'b') => out.push('\u{8}'),
            Some(b'f') => out.push('\u{c}'),
            Some(b'n') => out.push('\n'),
            Some(b'r') => out.push('\r'),
            Some(b't') => out.push('\t'),
            Some(b'u') => {
                let first = self.hex4()?;
                // The factory encodes with Python's default ensure_ascii, so every character above
                // the BMP arrives as a surrogate pair and the pair has to be rejoined here.
                let ch = if (0xD800..0xDC00).contains(&first) {
                    self.expect(b'\\')?;
                    self.expect(b'u')?;
                    let second = self.hex4()?;
                    if !(0xDC00..0xE000).contains(&second) {
                        return Err("high surrogate without a low one".to_string());
                    }
                    0x1_0000 + ((first - 0xD800) << 10) + (second - 0xDC00)
                } else if (0xDC00..0xE000).contains(&first) {
                    return Err("low surrogate without a high one".to_string());
                } else {
                    first
                };
                out.push(char::from_u32(ch).ok_or("escape is not a character")?);
            }
            _ => return Err(format!("bad escape at byte {}", self.pos)),
        }
        Ok(())
    }

    fn hex4(&mut self) -> Result<u32, String> {
        let end = self.pos + 4;
        if end > self.bytes.len() {
            return Err("truncated \\u escape".to_string());
        }
        let text = std::str::from_utf8(&self.bytes[self.pos..end])
            .map_err(|_| "bad \\u escape".to_string())?;
        let value = u32::from_str_radix(text, 16).map_err(|_| "bad \\u escape".to_string())?;
        self.pos = end;
        Ok(value)
    }
}

/// Read one complete JSON value, and insist it is the whole of the text.
pub fn parse(text: &str) -> Result<Json, String> {
    let mut parser = Parser { bytes: text.as_bytes(), pos: 0 };
    let value = parser.value(0)?;
    parser.skip_space();
    if parser.pos != parser.bytes.len() {
        return Err(format!("trailing text at byte {}", parser.pos));
    }
    Ok(value)
}

pub fn write(value: &Json, out: &mut String) {
    match value {
        Json::Null => out.push_str("null"),
        Json::Bool(true) => out.push_str("true"),
        Json::Bool(false) => out.push_str("false"),
        Json::Number(n) => {
            if n.is_finite() {
                // Rust's shortest round-tripping form, which prints a whole number without a
                // fractional part and so leaves an echoed integer id looking like an integer.
                let _ = write!(out, "{}", n);
            } else {
                // JSON has no NaN and no infinity. Writing Rust's spelling of them would put a
                // line on the wire that the factory cannot parse, which would lose the call
                // entirely; null at least arrives and compares.
                out.push_str("null");
            }
        }
        Json::String(s) => write_string(s, out),
        Json::Array(items) => {
            out.push('[');
            for (i, item) in items.iter().enumerate() {
                if i > 0 {
                    out.push(',');
                }
                write(item, out);
            }
            out.push(']');
        }
        Json::Object(pairs) => {
            out.push('{');
            for (i, (key, item)) in pairs.iter().enumerate() {
                if i > 0 {
                    out.push(',');
                }
                write_string(key, out);
                out.push(':');
                write(item, out);
            }
            out.push('}');
        }
    }
}

fn write_string(s: &str, out: &mut String) {
    out.push('"');
    for ch in s.chars() {
        match ch {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            '\u{8}' => out.push_str("\\b"),
            '\u{c}' => out.push_str("\\f"),
            c if c < ' ' => {
                let _ = write!(out, "\\u{:04x}", c as u32);
            }
            c => out.push(c),
        }
    }
    out.push('"');
}

fn reply_ok(id: &Json, key: &str, value: Json) -> String {
    let reply = Json::Object(vec![
        ("id".to_string(), id.clone()),
        ("ok".to_string(), Json::Bool(true)),
        (key.to_string(), value),
    ]);
    let mut out = String::new();
    write(&reply, &mut out);
    out
}

fn reply_err(id: &Json, message: &str) -> String {
    let reply = Json::Object(vec![
        ("id".to_string(), id.clone()),
        ("ok".to_string(), Json::Bool(false)),
        ("error".to_string(), Json::String(message.to_string())),
    ]);
    let mut out = String::new();
    write(&reply, &mut out);
    out
}

fn handle(request: &Json) -> String {
    let id = request.get("id").cloned().unwrap_or(Json::Null);
    // AN ARGS FIELD OF THE WRONG SHAPE IS A REFUSAL, NOT AN EMPTY CALL. Falling through to `[]` for
    // both cases is the most expensive kind of wrong: `{"args": "not-a-list"}` was quietly rewritten
    // into a call with no arguments, the subject answered whatever a no-argument call returns, and
    // the reply said ok:true. A false SUCCESS enters grading as though it were a real answer.
    //
    // A MISSING field keeps the empty default: the factory always sends `args`, so its absence is a
    // hand-written line rather than a malformed call.
    let empty = Json::Array(Vec::new());
    let args = match request.get("args") {
        Some(value @ Json::Array(_)) => value,
        None => &empty,
        Some(_) => return reply_err(&id, "the arguments must be a JSON array"),
    };
    let op = request.get("op").and_then(Json::as_str).unwrap_or("run");

    if op == "time" {
        // TIMED HERE, on this side of the pipe. Measuring from the factory would charge the subject
        // for process startup and for JSON transport, which for a quick subject is most of the
        // clock, and a compiled subject is exactly the quick case.
        let repeats = request.get("repeats").and_then(Json::as_f64).unwrap_or(1.0) as i64;
        let started = Instant::now();
        for _ in 0..repeats {
            if let Err(message) = attempt(args) {
                return reply_err(&id, &message);
            }
        }
        let elapsed = started.elapsed().as_secs_f64();
        return reply_ok(&id, "seconds", Json::Number(elapsed));
    }

    match attempt(args) {
        Ok(value) => reply_ok(&id, "value", value),
        // A REFUSAL IS AN ANSWER. How the subject rejects bad input is behaviour a reimplementation
        // has to reproduce, so it is reported and the loop carries on reading.
        Err(message) => reply_err(&id, &message),
    }
}

/// Call the subject, collapsing both of Rust's ways of failing into one description.
///
/// THE UNWIND CATCH IS NOT DEFENSIVE TIDINESS. A panic is how a great deal of Rust refuses -- an
/// index past the end of a slice, `unwrap` on None, a division by zero, an arithmetic overflow in a
/// debug build -- and without this it takes the process down and every probe queued behind it is
/// lost. Measured, before this existed: a subject panicking on one input answered probe 1 and was
/// never heard from again, so freeze discarded 47% to 100% of the corpus and refused the candidate
/// with `will-not-repeat-itself`. That reads as unusable material and was a missing seven lines here.
///
/// `AssertUnwindSafe` because the closure borrows `args`, which this function does not mutate and
/// does not hand out; there is nothing for a partially-unwound call to have left inconsistent.
fn attempt(args: &Json) -> Result<Json, String> {
    match panic::catch_unwind(AssertUnwindSafe(|| subject::entry(args))) {
        Ok(answered) => answered,
        Err(payload) => Err(describe_panic(&payload)),
    }
}

/// A caught panic as a one-line message -- and never as a backtrace.
///
/// A trace carries the absolute paths of the machine that produced it, and frozen into an expectation
/// those could not be reproduced anywhere else. The payload of a Rust panic is `&str` for a literal
/// message and `String` for a formatted one; anything else carries no text worth reporting.
fn describe_panic(payload: &Box<dyn std::any::Any + Send>) -> String {
    if let Some(text) = payload.downcast_ref::<&str>() {
        format!("panic: {}", text)
    } else if let Some(text) = payload.downcast_ref::<String>() {
        format!("panic: {}", text)
    } else {
        "panic: the subject panicked without a message".to_string()
    }
}

fn main() {
    let stdin = io::stdin();
    let stdout = io::stdout();
    let mut out = stdout.lock();

    // `lines` reassembles whatever the pipe delivered, so a probe larger than one read is not this
    // loop's problem. A line that is not valid UTF-8 cannot be a request and is skipped like any
    // other unreadable line.
    for line in stdin.lock().lines() {
        let line = match line {
            Ok(line) => line,
            Err(_) => continue,
        };
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        let request = match parse(line) {
            Ok(request @ Json::Object(_)) => request,
            _ => continue,                        // an unreadable line is not a call
        };

        // A closed pipe is the factory going away first, not this process failing, so it ends the
        // loop quietly instead of panicking inside a write.
        if writeln!(out, "{}", handle(&request)).is_err() || out.flush().is_err() {
            return;
        }
    }
}
