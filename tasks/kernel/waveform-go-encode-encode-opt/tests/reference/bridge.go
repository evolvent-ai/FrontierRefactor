package main

import "fmt"

func frfInts(value interface{}) ([]int, bool) {
	// A nil slice and an empty one are different values to a subject that checks len() against
	// nil, so an empty JSON array becomes an allocated slice of length zero rather than nil.
	items, ok := value.([]interface{})
	if !ok {
		return nil, false
	}
	out := make([]int, 0, len(items))
	for _, item := range items {
		converted, ok := frfInt(item)
		if !ok {
			return nil, false
		}
		out = append(out, converted)
	}
	return out, true
}

func frfInt(value interface{}) (int, bool) {
	// JSON has one number type and Go's decoder hands it over as float64, so every integer
	// argument arrives needing this. A non-integral float is REFUSED rather than truncated:
	// silently dropping .5 would make the subject answer a question it was not asked.
	number, ok := value.(float64)
	if !ok || number != float64(int(number)) {
		return 0, false
	}
	return int(number), true
}

// Entry is what serve.go calls. See frf/observe/call/bridge.py.
func Entry(args []interface{}) (interface{}, error) {
	if len(args) != 1 {
		return nil, fmt.Errorf("expected 1 argument(s), got %d", len(args))
	}
	arg0, ok0 := frfInts(args[0])
	if !ok0 {
		return nil, fmt.Errorf("argument 0 is not a int_array")
	}
	return Encode(arg0), nil
}
