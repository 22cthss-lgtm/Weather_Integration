import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.config import load_backend_env


class BackendEnvConfigTests(unittest.TestCase):
    def test_load_backend_env_reads_cwa_api_key_from_dotenv_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text("CWA_API_KEY=dotenv-test-key\n", encoding="utf-8")

            with patch.dict(os.environ, {}, clear=True):
                load_backend_env(env_path)

                self.assertEqual(os.getenv("CWA_API_KEY"), "dotenv-test-key")


if __name__ == "__main__":
    unittest.main()
