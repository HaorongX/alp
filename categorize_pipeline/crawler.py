import requests
import os

def crawl(url, name):
    os.system(f"wget {url} -O {name}.pdf")
    print(f"Downloaded {name}")

def __main__():
    os.system("export Headers='User-Agent: Mozilla/5.0 (Windows NT 6.0) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.97 Safari/537.11'")
    base_url = '''https://pastpapers.papacambridge.com/download_file.php\\?files\\=https://pastpapers.papacambridge.com/directories/CAIE/CAIE-pastpapers/upload/9618_'''
    
    series = ["s"]
    years = ["22"]
    papers = ["qp", "ms"]
    qp = ["1", "2", "3"]
    varients = ["1", "2", "3"]

    for s in series:
        for y in years:
            for p in papers:
                for q in qp:
                    for v in varients:
                        url = f"{base_url}{s}{y}_{p}_{q}{v}.pdf"
                        name = f"9618_{s}{y}_{p}_{q}{v}"
                        # print(f"{url} \n {name}")
                        crawl(url, name)

if __name__ == "__main__":
    # https://pastpapers.papacambridge.com/download_file.php\?files\=https://pastpapers.papacambridge.com/directories/CAIE/CAIE-pastpapers/upload/9618_s21_qp_11.pdf
    __main__()