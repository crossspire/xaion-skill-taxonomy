import os
from typing import Optional

import pandas as pd
import sqlalchemy
from sqlalchemy.engine import Connection


class PostgresDB:
    def __init__(
        self, hostname: str, database: str, username: str, password: str, port: int
    ) -> None:
        self.hostname = hostname
        self.database = database
        self.username = username
        self.password = password
        self.port = port
        self.engine: Optional[sqlalchemy.engine.Engine] = None
        self.connection: Optional[Connection] = None

    def connect(self) -> None:
        """データベースに接続する"""
        try:
            self.engine = sqlalchemy.create_engine(
                f"postgresql://{self.username}:{self.password}@{self.hostname}:{self.port}/{self.database}"
            )
            self.connection = self.engine.connect()
            print("データベースに接続しました")
        except Exception as e:
            print(f"接続エラー: {e}")

    def execute_query(self, query: str) -> Optional[pd.DataFrame]:
        """SQLクエリを実行し、結果をデータフレームで返す"""
        if self.connection is None:
            print("データベースに接続されていません")
            return None

        try:
            df = pd.read_sql_query(query, self.connection)
            return df
        except Exception as e:
            print(f"クエリエラー: {e}")
            return None

    def close(self) -> None:
        """データベース接続を閉じる"""
        if self.connection is not None:
            self.connection.close()
            print("データベース接続を閉じました")
        else:
            print("接続が存在しません")



def setup_db() -> PostgresDB:
    db = PostgresDB(
        os.environ["DB_HOSTNAME"],
        os.environ["DB_DATABASENAME"],
        os.environ["DB_USERNAME"],
        os.environ["DB_PASSWORD"],
        int(os.environ["DB_PORT"]),
    )
    db.connect()
    return db


def teardown_db(db: PostgresDB) -> None:
    db.close()
