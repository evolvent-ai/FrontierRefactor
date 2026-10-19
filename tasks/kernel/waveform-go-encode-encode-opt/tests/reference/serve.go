// Serve a Go subject over the wire. Written into the task; not imported by the factory.
//
// Go has no dynamic import, so a subject cannot be loaded at run time the way the Python shim loads
// its module. The convention here is instead that the subject is compiled into this same package and
// supplies
//
//	func Entry(args []interface{}) (interface{}, error)
//
// answering with a value or refusing with an error. Everything else -- the framing, the refusal
// path, the clock -- is this file.
package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"time"
)

// A Scanner stops silently at a line longer than its buffer, reporting it as an ordinary end of
// input, and its default limit of 64 KiB is smaller than the argument lists this wire legitimately
// carries. Raised well past any plausible probe, since the failure it prevents is a mute one.
const maxRequestLine = 16 * 1024 * 1024

// request is one call to make.
//
// ID is kept as raw JSON and echoed back byte for byte: decoded into a Go number it would arrive as
// a float64, whose mantissa cannot hold every integer a caller might number a request with.
//
// Call names the entry point. A single-function subject has exactly one, so the field is read and
// ignored; it exists for a subject that later has more than one.
type request struct {
	ID      json.RawMessage `json:"id"`
	Op      string          `json:"op"`
	Call    string          `json:"call"`
	Args    []interface{}   `json:"args"`
	Repeats int             `json:"repeats"`
}

func main() {
	// Lines are scanned and then unmarshalled one at a time rather than pulled off a json.Decoder
	// wrapped round stdin. A Decoder would also read a stream of objects, but it cannot be
	// resynchronised after a syntax error -- the remainder of the bad line is still in front of it,
	// so a single malformed line would poison every call behind it. The rule is that an unreadable
	// line is skipped and the next one is served as normal, and that needs the line boundaries to
	// be real.
	scanner := bufio.NewScanner(os.Stdin)
	scanner.Buffer(make([]byte, 0, 64*1024), maxRequestLine)
	for scanner.Scan() {
		// Decoded through a POINTER so that a bare `null` line is skipped rather than served.
		// Unmarshalling null into a struct succeeds and leaves every field at its zero value, which
		// would be answered as though it were a call and put an unmatched extra line on the wire;
		// into a pointer it sets nil instead, and any other non-object still fails outright.
		// Decoded in two steps, because "this line is not a call" and "this call's fields are the
		// wrong shape" are different facts and only the first may be answered with silence.
		//
		// A single strict decode conflated them. `args` arriving as a string rather than an array
		// fails to unmarshal into the struct, so a line that carried an id -- a real call, from the
		// factory, waiting for a reply -- was skipped without a word, and the factory then blocked
		// on that id until PROBE_TIMEOUT, which defaults to two minutes. Python and JavaScript both
		// answer the same line with a refusal. `write` below already states the rule this restores:
		// writing nothing leaves the factory blocked on a line that never arrives.
		var loose map[string]json.RawMessage
		if err := json.Unmarshal(scanner.Bytes(), &loose); err != nil || loose == nil {
			continue // not a JSON object, so not a call: nothing is owed
		}
		var req *request
		if err := json.Unmarshal(scanner.Bytes(), &req); err != nil || req == nil {
			// An object, so a call -- one this shim cannot make sense of. The id is echoed from the
			// raw bytes so that a reply can still be matched to its request.
			write(map[string]interface{}{
				"id":    loose["id"],
				"ok":    false,
				"error": fmt.Sprintf("the arguments must be a JSON array: %v", err),
			})
			continue
		}
		write(serve(*req))
	}
	if err := scanner.Err(); err != nil {
		// stdout carries answers and nothing else, so stderr is the only place this can be said.
		// The factory reads it when the subject stops answering, and a line that was too long to
		// read would otherwise look like an ordinary end of input.
		fmt.Fprintf(os.Stderr, "serve: reading stdin: %v\n", err)
		os.Exit(1)
	}
	// End of input is the factory closing the pipe, which is an ordinary shutdown.
}

// serve answers one request.
//
// The reply is a map rather than a struct because `value` has to appear even when it is null, false
// or zero: the factory fingerprints the reply once decoded, so a field left out and a field holding
// null are two different answers, and `omitempty` would quietly turn one into the other.
func serve(req request) map[string]interface{} {
	if req.Op == "time" {
		repeats := req.Repeats
		if repeats < 1 {
			// The field is absent on a run request and so decodes to zero. Timing zero calls would
			// report zero seconds, which reads as an infinitely fast subject rather than a mistake.
			repeats = 1
		}
		// TIMED HERE, on this side of the pipe. Measured from the factory the subject would be
		// charged for process startup and for JSON transport, and for the quick subjects this
		// pipeline mostly produces that overhead is most of what the clock would see.
		started := time.Now()
		for i := 0; i < repeats; i++ {
			if _, failure := attempt(req.Args); failure != "" {
				return map[string]interface{}{"id": req.ID, "ok": false, "error": failure}
			}
		}
		elapsed := time.Since(started)
		return map[string]interface{}{"id": req.ID, "ok": true, "seconds": elapsed.Seconds()}
	}
	value, failure := attempt(req.Args)
	if failure != "" {
		// A REFUSAL IS AN ANSWER. How the subject rejects bad input is behaviour a reimplementation
		// has to reproduce, so it is reported and the next line is read.
		return map[string]interface{}{"id": req.ID, "ok": false, "error": failure}
	}
	return map[string]interface{}{"id": req.ID, "ok": true, "value": value}
}

// attempt calls the subject and collapses both of Go's ways of failing into one description, empty
// when the call returned.
//
// The recover is not defensive tidiness: a panic is how a great deal of Go refuses, whether an index
// out of range or a type assertion on an argument that arrived as the wrong shape, and it has to
// reach the factory as an answer rather than take the process down and lose the rest of the corpus.
func attempt(args []interface{}) (value interface{}, failure string) {
	defer func() {
		if recovered := recover(); recovered != nil {
			value, failure = nil, describe(recovered)
		}
	}()
	result, err := Entry(args)
	if err != nil {
		return nil, err.Error()
	}
	return result, ""
}

// describe renders a recovered panic as "TypeName: message" -- and never as a stack trace.
//
// A trace carries the absolute paths of the machine that produced it. Frozen into an expectation,
// those paths could not be reproduced on any other machine.
//
// A RETURNED ERROR IS DESCRIBED BY ITS MESSAGE ALONE, and that asymmetry with the panic case is
// deliberate. Go's concrete error types are an implementation detail of how an error was built:
// errors.New gives *errors.errorString and fmt.Errorf gives *fmt.wrapError for what is, to a
// caller, the same refusal. Freezing the type would make a reimplementation that says the same
// thing with the other constructor fail a corpus it behaves identically on. A panic is different:
// its value can be any type at all, the type is often the whole of the information -- a
// runtime.Error for an index out of range -- and there is no message without it.
func describe(failure interface{}) string {
	return fmt.Sprintf("%T: %v", failure, failure)
}

// write puts one reply on stdout, and only ever one line of it.
//
// os.Stdout is unbuffered in Go, so the write is the flush; wrapping it in a bufio.Writer would
// leave the factory waiting on a reply that had already been produced.
func write(reply map[string]interface{}) {
	body, err := json.Marshal(reply)
	if err != nil {
		// The subject answered with something JSON cannot carry: a channel, a function, a NaN. That
		// is an answer which failed to encode rather than a broken wire, so it is reported as a
		// refusal. Writing nothing would leave the factory blocked on a line that never arrives.
		body, err = json.Marshal(map[string]interface{}{
			"id":    reply["id"],
			"ok":    false,
			"error": fmt.Sprintf("the returned value could not be encoded as JSON: %v", err),
		})
	}
	if err != nil {
		body = []byte(`{"ok":false,"error":"the reply could not be encoded as JSON"}`)
	}
	os.Stdout.Write(append(body, '\n'))
}
