import io
import sys


class PythonContext:
    def __init__(self):
        self.globals = {}
        self.globals["final_answer"] = self._final_answer
        self.has_final_answer = False
        self.final_answer_value = None

    def clear_final_answer(self):
        self.has_final_answer = False
        self.final_answer_value = None

    def _final_answer(self, value: str):
        self.has_final_answer = True
        self.final_answer_value = value

    def run(self, code) -> tuple[str, str]:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = sys_out = io.StringIO()
        sys.stderr = sys_err = io.StringIO()

        try:
            exec(code, self.globals)
        except Exception as e:
            print(f"Error during execution: {e}", file=sys.stderr)
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        return sys_out.getvalue(), sys_err.getvalue()
