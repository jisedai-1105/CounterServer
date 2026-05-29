import logging
import os
from datetime import datetime


class DailyFileHandler(logging.FileHandler):
    """日付が変わったら自動的に新しいログファイルに切り替えるハンドラ"""

    def __init__(self, log_dir, log_name, encoding="utf-8"):
        self.log_dir = log_dir
        self.log_name = log_name
        self.current_date = self._today()
        log_path = self._build_path()
        super().__init__(log_path, encoding=encoding)

    def _today(self) -> str:
        return datetime.now().strftime("%Y%m%d")

    def _build_path(self) -> str:
        # ファイル名の拡張子の前に日付を挿入: app.log → app_20250529.log
        base, ext = os.path.splitext(self.log_name)
        filename = f"{base}_{self.current_date}{ext}"
        return os.path.join(self.log_dir, filename)

    def emit(self, record):
        """ログ出力のたびに日付をチェックし、変わっていればファイルを切り替える"""
        today = self._today()
        if today != self.current_date:
            self.current_date = today
            new_path = self._build_path()
            self.stream.close()
            self.baseFilename = os.path.abspath(new_path)
            self.stream = self._open()
        super().emit(record)


class AppLogger:
    def __init__(self, log_dir="./app", log_name="app.log"):

        # ログフォルダ作成
        os.makedirs(log_dir, exist_ok=True)

        # ロガー作成
        self.logger = logging.getLogger("AppLogger")
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False

        # すでにハンドラがある場合は重複追加しない
        if not self.logger.handlers:

            # フォーマット
            formatter = logging.Formatter(
                "【%(asctime)s】[%(levelname)s] %(message)s"
            )

            # コンソール出力
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

            # ファイル出力（日付付きファイル名、日付変わりで自動切替）
            file_handler = DailyFileHandler(log_dir, log_name, encoding="utf-8")
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def info(self, msg: str):
        self.logger.info(msg)

    def warning(self, msg: str):
        self.logger.warning(msg)

    def error(self, msg: str):
        self.logger.error(msg)

    def debug(self, msg: str):
        self.logger.debug(msg)


# ---------------------------------------------------------
# 単体実行テスト
# ---------------------------------------------------------
if __name__ == "__main__":
    log = AppLogger(log_dir="./app", log_name="test.log")

    log.info("ログクラスのテスト開始")
    log.warning("これは警告ログです")
    log.error("これはエラーログです")
    log.debug("これはデバッグログです")

    print("ログ出力テスト完了。./app/test_YYYYMMDD.log を確認してください。")