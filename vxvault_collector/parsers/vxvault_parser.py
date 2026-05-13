from bs4 import BeautifulSoup
from models.ioc import IOCRecord

def parse(html):
    soup = BeautifulSoup(html, "lxml")
    table = soup.select_one("#page table")
    if not table:
        return []

    out = []
    for tr in table.select("tr"):
        tds = tr.find_all("td")
        if len(tds) != 5:
            continue

        details_id = ""
        link = tr.select_one('a[href*="ViriFiche.php?ID="]')
        if link and "ID=" in link["href"]:
            details_id = link["href"].split("ID=")[-1].split("&")[0]

        url = tds[1].text.strip()
        if url.startswith("[D] "):
            url = url[4:].strip()
        out.append(IOCRecord(
            date=tds[0].text.strip(),
            url=url,
            md5=tds[2].text.strip(),
            ip=tds[3].text.strip(),
            tools=tds[4].text.strip(),
            details_id=details_id,
            filename=url.split("/")[-1] if "/" in url else ""
        ))
    return out

def parse_details(html, record):
    soup = BeautifulSoup(html, "lxml")
    page = soup.select_one("#page")
    if not page:
        return record
    
    # Tüm linkleri çek (Tools links)
    links = []
    for a in page.select("a"):
        if any(x in a.text for x in ["[VT]", "[VirusTotal]", "[PEDump]", "[TR]", "[Triage]"]):
            links.append(f"{a.text}:{a['href']}")
    record.tools_links = "\n".join(links)

    text = page.get_text(separator="|")
    parts = [p.strip() for p in text.split("|")]
    
    for i, p in enumerate(parts):
        if "File:" in p and i+1 < len(parts):
            record.filename = parts[i+1]
        if "Size:" in p and i+1 < len(parts):
            record.size = parts[i+1]
        if "MD5:" in p and i+1 < len(parts):
            record.md5 = parts[i+1]
        if "SHA-1:" in p and i+1 < len(parts):
            record.sha1 = parts[i+1]
        if "SHA-256:" in p and i+1 < len(parts):
            record.sha256 = parts[i+1]

    # Ekstra kontrol: Eğer parçalarda bulunamadıysa düz metinde ara
    raw_text = page.get_text()
    if not record.sha256 and "SHA-256:" in raw_text:
        record.sha256 = raw_text.split("SHA-256:")[1].split("\n")[0].strip()
    if not record.md5 and "MD5:" in raw_text:
        record.md5 = raw_text.split("MD5:")[1].split("\n")[0].strip()
    if not record.size and "Size:" in raw_text:
        record.size = raw_text.split("Size:")[1].split("\n")[0].strip()
        
    return record
