import yaml
import os

class YAMLReader:
    @staticmethod
    def read(file_path):
        """Baca 1 file YAML"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File YAML tidak ditemukan: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)


