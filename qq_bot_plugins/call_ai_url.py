import requests
import json
import re
from bs4 import BeautifulSoup

# 域名黑名单
BLACKLIST_DOMAINS = [
    'zhihu.com',
    'zhihu.org',
    'zhihu.io'
]

def url_query(url):
    """
    访问指定URL并返回处理后的内容
    
    参数:
    url (str): 目标URL
    
    返回:
    dict: 包含状态、内容和相关信息的字典
    """
    # 模拟不同浏览器的User-Agent列表
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
    ]
    
    try:
        # 黑名单检查
        import urllib.parse
        parsed_url = urllib.parse.urlparse(url)
        domain = parsed_url.netloc
        for black_domain in BLACKLIST_DOMAINS:
            if black_domain in domain:
                return {
                    "status": "error",
                    "error": "域名在黑名单中，无法访问，请勿尝试继续访问该网站",
                    "url": url
                }
        
        # 确保URL格式正确
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        
        # 设置请求头
        headers = {
            'User-Agent': USER_AGENTS[hash(url) % len(USER_AGENTS)],  # 基于URL选择相对固定的User-Agent
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.3,en;q=0.2'
        }
        
        # 发送请求并获取内容
        response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
        response.raise_for_status()
        
        # 获取基本信息
        content_type = response.headers.get('Content-Type', '')
        status_code = response.status_code
        final_url = response.url
        
        # 根据内容类型进行适当的处理
        if 'text/html' in content_type:
            # 对HTML内容进行简单清洗
            soup = BeautifulSoup(response.text, 'html.parser')
            for script in soup(['script', 'style']):
                script.decompose()
            text = soup.get_text(separator='\n', strip=True)
            cleaned_content = re.sub(r'\s+', ' ', text)
        elif 'application/json' in content_type:
            # JSON内容直接解析
            try:
                json_data = response.json()
                cleaned_content = json.dumps(json_data, ensure_ascii=False, indent=2)
            except json.JSONDecodeError:
                cleaned_content = response.text
        else:
            # 其他类型内容简单处理
            cleaned_content = re.sub(r'<[^>]+>', '', response.text)
        
        return {
            "status": "success",
            "url": url,
            "final_url": final_url,
            "status_code": status_code,
            "content_type": content_type,
            "content": cleaned_content
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "url": url
        }