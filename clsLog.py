import logging
import os
from datetime import datetime

class AppLogger:
    def __init__(self, log_dir="logs", log_name="app.log"):

        # ログフォルダ作成
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        # ログファイルのフルパス
        self.log_path = os.path.join(log_dir, log_name)

        # ロガー作成
        self.logger = logging.getLogger("AppLogger")
        #self.logger.setLevel(logging.INFO)
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

            # ファイル出力
            file_handler = logging.FileHandler(self.log_path, encoding="utf-8")
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
    log = AppLogger(log_dir="/app", log_name="test.log")

    log.info("ログクラスのテスト開始")
    log.warning("これは警告ログです")
    log.error("これはエラーログです")

    print("ログ出力テスト完了。test_logs/test.log を確認してください。")
