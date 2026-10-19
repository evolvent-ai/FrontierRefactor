
class Ex15 {
	public static int[] histogram(int[] a, int M) {
		int[] result = new int[M];
		for (int i = 0; i < a.length; i++) {
			if (a[i] >= 0 && a[i] < M) {
				result[a[i]]++;
			}
		}
		return result;
	}

	public static void main(String[] args) {
		int[] a = { 1, 1, 2, 3, 1, 7, 5, 3, 2, 2, 2 };
		int[] result = histogram(a, 8);
		for (int i = 0; i < result.length; i++) {
			System.out.printf("%3d", result[i]);
		}
	}
}

// --- frf call bridge (generated) ---
public class Subject {
    static long[] frfInts(Object value) {
        if (!(value instanceof java.util.List)) throw new IllegalArgumentException("expected an array");
        java.util.List<?> items = (java.util.List<?>) value;
        long[] out = new long[items.size()];
        for (int i = 0; i < out.length; i++) out[i] = frfInt(items.get(i));
        return out;
    }
    static long frfInt(Object value) {
        // The shim's parser yields Long for an integral token and Double otherwise, so both arrive
        // here. A non-integral value is REFUSED rather than truncated.
        if (!(value instanceof Number)) throw new IllegalArgumentException("expected an integer");
        double number = ((Number) value).doubleValue();
        if (number != Math.rint(number)) throw new IllegalArgumentException("expected an integer");
        return (long) number;
    }
    static java.util.List<Object> frfBox(int[] items) {
        java.util.List<Object> out = new java.util.ArrayList<Object>();
        for (int item : items) out.add(Long.valueOf(item));
        return out;
    }

    // entry is what Serve.java reflects for. See frf/observe/call/bridge.py.
    public static Object entry(java.util.List<Object> args) {
        if (args.size() != 2) {
            throw new IllegalArgumentException("expected 2 argument(s), got " + args.size());
        }
        long[] arg0 = frfInts(args.get(0));
        int[] arg0c = new int[arg0.length];
        for (int i = 0; i < arg0.length; i++) arg0c[i] = (int) arg0[i];
        long arg1 = frfInt(args.get(1));
        int arg1c = (int) arg1;
        int[] value = Ex15.histogram(arg0c, arg1c);
        return frfBox(value);
    }
}