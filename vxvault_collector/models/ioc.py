from dataclasses import dataclass

@dataclass
class IOCRecord:
    date: str
    url: str
    md5: str
    ip: str
    tools: str
    details_id: str = ""
    sha1: str = ""
    sha256: str = ""
    size: str = ""
    filename: str = ""
    tools_links: str = "" # JSON veya string listesi olarak linkler
