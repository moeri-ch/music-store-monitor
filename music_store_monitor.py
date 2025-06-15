#!/usr/bin/env python3
"""
価格必須版5つの楽器店サイト統合監視プログラム (GitHub Actions対応・改良版)
毎日実行・10万円以上の商品のみ・キーワード検出機能付き
"""

import requests
from bs4 import BeautifulSoup
import json
import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging
import os
import sys
import time
from urllib.parse import urljoin, urlparse

class PriceRequiredMultiStoreMusicMonitor:
    def __init__(self):
        """5つの楽器店統合監視システム（価格必須版・改良版）"""
        self.stores = {
            'ikebe': {
                'name': 'イケベ楽器店',
                'url': 'https://www.ikebe-gakki.com/Form/Product/ProductList.aspx?shop=0&cat=agt003&bid=ec&dpcnt=20&img=1&sort=07&udns=1&fpfl=0&sfl=0&pno=1',
                'base_url': 'https://www.ikebe-gakki.com'
            },
            'kurosawa': {
                'name': '黒澤楽器店',
                'url': 'https://shop.kurosawagakki.com/items/search/classic-guitar',
                'base_url': 'https://shop.kurosawagakki.com'
            },
            'shimamura': {
                'name': '島村楽器',
                'url': 'https://store.shimamura.co.jp/ec/Facet?category_0=11040000000',
                'base_url': 'https://store.shimamura.co.jp'
            },
            'qsic': {
                'name': 'QSic',
                'url': 'https://www.qsic.jp/?mode=cate&cbid=790427&csid=0&sort=n',
                'base_url': 'https://www.qsic.jp'
            },
            'jguitar': {
                'name': 'J-Guitar',
                'url': 'https://www.j-guitar.com/products/list.php?category_id=103&category_id1=1',
                'base_url': 'https://www.j-guitar.com'
            }
        }
        
        self.data_file = 'multi_store_products_price_required.json'
        self.config = self.load_config()
        self.setup_logging()
        self.special_keywords = ['ダブルトップ', 'ラティス', 'doubletop', 'lattice']
        
    def load_config(self):
        """設定を環境変数またはファイルから読み込み"""
        if os.getenv('GITHUB_ACTIONS'):
            print("🔧 GitHub Actions環境で実行中")
            
            # 環境変数の存在確認
            required_vars = ['SENDER_EMAIL', 'SENDER_PASSWORD', 'RECIPIENT_EMAIL']
            missing_vars = [var for var in required_vars if not os.getenv(var)]
            
            if missing_vars:
                error_msg = f"❌ 必要な環境変数が設定されていません: {missing_vars}"
                print(error_msg)
                raise ValueError(error_msg)
            
            config = {
                "email": {
                    "smtp_server": os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
                    "smtp_port": int(os.getenv('SMTP_PORT', 587)),
                    "sender_email": os.getenv('SENDER_EMAIL'),
                    "sender_password": os.getenv('SENDER_PASSWORD'),
                    "recipient_email": os.getenv('RECIPIENT_EMAIL')
                }
            }
            
            print(f"✅ 設定読み込み完了:")
            print(f"  SMTP Server: {config['email']['smtp_server']}")
            print(f"  SMTP Port: {config['email']['smtp_port']}")
            print(f"  Sender Email: {config['email']['sender_email']}")
            print(f"  Recipient Email: {config['email']['recipient_email']}")
            
            return config
        else:
            print("🔧 ローカル環境で実行中")
            try:
                with open('config.json', 'r', encoding='utf-8') as f:
                    return json.load(f)
            except FileNotFoundError:
                print("❌ config.jsonが見つかりません")
                print("ローカル実行する場合は、config.json.templateを参考にconfig.jsonを作成してください")
                sys.exit(1)
    
    def setup_logging(self):
        """ログ設定"""
        log_filename = 'multi_store_monitor_price_required.log'
        
        # ログファイルを確実に作成
        try:
            with open(log_filename, 'a', encoding='utf-8') as f:
                f.write(f"\n=== ログ開始: {datetime.now()} ===\n")
        except Exception as e:
            print(f"ログファイル作成エラー: {e}")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(log_filename, encoding='utf-8')
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        if os.getenv('GITHUB_ACTIONS'):
            self.logger.info("🚀 GitHub Actions で5サイト統合楽器店監視を開始（毎日・10万円以上・改良版）")
        else:
            self.logger.info("🚀 ローカル環境で5サイト統合楽器店監視を開始")
    
    def extract_price_value(self, price_str):
        """価格文字列から数値を抽出"""
        if not price_str:
            return 0
        
        # 数字とカンマのみを抽出
        numbers = re.findall(r'[\d,]+', price_str)
        if numbers:
            try:
                return int(numbers[0].replace(',', ''))
            except ValueError:
                return 0
        return 0
    
    def is_high_value_product(self, product):
        """10万円以上の商品かチェック"""
        price_value = self.extract_price_value(product.get('price', ''))
        return price_value >= 100000
    
    def has_special_keywords(self, product_name):
        """特別なキーワード（ダブルトップ、ラティス）が含まれているかチェック"""
        name_lower = product_name.lower()
        return any(keyword.lower() in name_lower for keyword in self.special_keywords)
    
    def get_all_products(self):
        """全ての楽器店から商品データを取得"""
        all_products = {}
        total_products = 0
        
        for store_key, store_info in self.stores.items():
            self.logger.info(f"🔍 {store_info['name']}の商品を取得中...")
            
            try:
                products = self.get_products_by_store(store_key, store_info)
                all_products[store_key] = products
                total_products += len(products)
                
                self.logger.info(f"✅ {store_info['name']}: {len(products)}件の商品を取得（価格付きのみ）")
                
                # 最初の数件をログ出力
                for i, product in enumerate(products[:3]):
                    self.logger.info(f"  {i+1}. {product['name'][:50]}... ({product['price']})")
                
                if len(products) > 3:
                    self.logger.info(f"     ...他 {len(products) - 3}件")
                
                # サイトへの負荷軽減のため少し待機
                time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"❌ {store_info['name']}でエラー: {e}")
                all_products[store_key] = []
        
        self.logger.info(f"🎯 全サイト合計: {total_products}件の商品を取得（価格付きのみ）")
        return all_products
    
    def get_products_by_store(self, store_key, store_info):
        """店舗別の商品データ取得"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(store_info['url'], headers=headers, timeout=30)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            raise Exception(f"HTTPエラー: {response.status_code}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 店舗別の修正されたスクレイピングロジック
        if store_key == 'ikebe':
            return self.parse_ikebe_products(soup, store_info['base_url'])
        elif store_key == 'kurosawa':
            return self.parse_kurosawa_products_fixed(soup, store_info['base_url'])
        elif store_key == 'shimamura':
            return self.parse_shimamura_products(soup, store_info['base_url'])
        elif store_key == 'qsic':
            return self.parse_qsic_products_fixed(soup, store_info['base_url'])
        elif store_key == 'jguitar':
            return self.parse_jguitar_products_improved(soup, store_info['base_url'])
        else:
            return []
    
    def parse_ikebe_products(self, soup, base_url):
        """イケベ楽器店の商品解析（価格必須）"""
        products = []
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            if self.is_ikebe_product_link(href, text):
                price_info = self.find_nearby_price(link)
                
                # 価格が見つからない場合はスキップ
                if not price_info or price_info == "価格確認中":
                    continue
                
                product = self.create_product_info(
                    store='ikebe',
                    name=text,
                    price=price_info,
                    link=urljoin(base_url, href),
                    store_name='イケベ楽器店'
                )
                
                if self.is_valid_product(product):
                    products.append(product)
        
        return products
    
    def parse_kurosawa_products_fixed(self, soup, base_url):
        """黒澤楽器店の修正版商品解析（価格必須）"""
        products = []
        text_content = soup.get_text()
        
        # テキストを行に分割
        lines = [line.strip() for line in text_content.split('\n') if line.strip()]
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # ブランド名を検出（単独行または短い行）
            brand_patterns = ['Juan Hernandez', 'Gibson', 'Cordoba', 'ARIA', 'YAMAHA', 'その他', '桜井 正毅']
            if any(brand in line for brand in brand_patterns) and len(line.split()) <= 4:
                brand = line
                
                # 次の行で商品名を探す
                if i + 1 < len(lines):
                    product_name_line = lines[i + 1]
                    
                    # 明らかに商品名ではない行をスキップ
                    if any(skip in product_name_line.lower() for skip in ['在庫', '状態', 'ポイント', '送料']):
                        i += 1
                        continue
                    
                    # 価格を探す（数行先まで）- 必須条件
                    price = None
                    
                    for j in range(i + 1, min(i + 8, len(lines))):
                        if j < len(lines):
                            if re.search(r'¥\s*[\d,]+', lines[j]):
                                price_match = re.search(r'¥\s*([\d,]+)', lines[j])
                                if price_match:
                                    price = f"¥{price_match.group(1)}"
                                break
                    
                    # 価格が見つからない場合はスキップ
                    if not price:
                        i += 2
                        continue
                    
                    # 商品URLを探す
                    product_links = soup.find_all('a', href=lambda x: x and '/items/' in x)
                    product_url = base_url  # デフォルト
                    
                    if product_links and len(products) < len(product_links):
                        product_url = urljoin(base_url, product_links[len(products)].get('href', ''))
                    
                    # 商品情報を作成
                    full_name = f"{brand} {product_name_line}".strip()
                    
                    product = self.create_product_info(
                        store='kurosawa',
                        name=full_name,
                        price=price,
                        link=product_url,
                        store_name='黒澤楽器店'
                    )
                    
                    if self.is_valid_product(product):
                        products.append(product)
                    
                    i += 2  # ブランド行と商品名行をスキップ
                else:
                    i += 1
            else:
                i += 1
        
        return products[:15]  # 最大15件に制限
    
    def parse_shimamura_products(self, soup, base_url):
        """島村楽器の商品解析（価格必須）"""
        products = []
        product_links = soup.find_all('a', href=lambda x: x and '/ec/pro/disp/' in x)
        
        for link in product_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            if text and len(text) > 5 and not any(skip in text.lower() for skip in ['送料', '出品', 'webshop']):
                price_info = self.find_nearby_price(link)
                
                # 価格が見つからない場合はスキップ
                if not price_info or price_info == "価格確認中":
                    continue
                
                product = self.create_product_info(
                    store='shimamura',
                    name=text,
                    price=price_info,
                    link=urljoin(base_url, href),
                    store_name='島村楽器'
                )
                
                if self.is_valid_product(product):
                    products.append(product)
        
        return products
    
    def parse_qsic_products_fixed(self, soup, base_url):
        """QSicの修正版商品解析（価格必須）"""
        products = []
        text_content = soup.get_text()
        
        # QSicの商品パターンを正確に解析
        lines = [line.strip() for line in text_content.split('\n') if line.strip()]
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # 商品名パターンを検出（【返品OK】を含む行）
            if '【返品OK】' in line and '[' in line and ']' in line:
                # 商品名部分を抽出（【返品OK】より前）
                product_name = line.split('【返品OK】')[0].strip()
                
                # 状態と説明を探す（次の行）
                condition = ""
                description = ""
                if i + 1 < len(lines) and lines[i + 1].startswith('[') and ']' in lines[i + 1]:
                    condition_line = lines[i + 1]
                    condition_match = re.search(r'\[([^\]]+)\]', condition_line)
                    if condition_match:
                        condition = condition_match.group(1)
                    description = condition_line.split(']', 1)[-1].strip()
                
                # 価格を探す（次の数行で）- 必須条件
                price = None
                for j in range(i + 1, min(i + 4, len(lines))):
                    if j < len(lines) and '円(税込)' in lines[j]:
                        price_match = re.search(r'([\d,]+)円\(税込\)', lines[j])
                        if price_match:
                            price = f"¥{price_match.group(1)}"
                        break
                
                # 価格が見つからない場合はスキップ
                if not price:
                    i += 1
                    continue
                
                # 完全な商品名を作成
                full_name = product_name
                if condition:
                    full_name += f" [{condition}]"
                if description:
                    full_name += f" {description}"
                
                product = self.create_product_info(
                    store='qsic',
                    name=full_name,
                    price=price,
                    link=base_url,
                    store_name='QSic'
                )
                
                if self.is_valid_product(product):
                    products.append(product)
                
                i += 3  # 商品名、状態、価格行をスキップ
            else:
                i += 1
        
        return products
    
    def parse_jguitar_products_improved(self, soup, base_url):
        """J-Guitarの大幅改良版商品解析（商品名抽出を大幅改善）"""
        products = []
        
        # 商品リンクを直接探す
        product_links = soup.find_all('a', href=lambda x: x and ('detail' in x or 'product' in x))
        
        # テーブル構造を解析
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                
                if len(cells) >= 2:
                    # 商品名候補を検索
                    product_name = None
                    price = None
                    product_url = base_url
                    
                    for cell in cells:
                        cell_text = cell.get_text(strip=True)
                        
                        # 商品名の判定ロジックを改善
                        if self.is_likely_jguitar_product_name(cell_text):
                            product_name = cell_text
                            
                            # 同じセルまたは近くのセルで価格を探す
                            price = self.find_price_in_cell_or_nearby(cell, row)
                            
                            # リンクを探す
                            link = cell.find('a', href=True)
                            if link:
                                product_url = urljoin(base_url, link['href'])
                            
                            break
                    
                    # 価格が見つからない場合、行全体で再検索
                    if product_name and not price:
                        for cell in cells:
                            price = self.extract_price_from_text(cell.get_text())
                            if price:
                                break
                    
                    # 商品として有効かチェック
                    if product_name and price:
                        product = self.create_product_info(
                            store='jguitar',
                            name=product_name,
                            price=price,
                            link=product_url,
                            store_name='J-Guitar'
                        )
                        
                        if self.is_valid_product(product):
                            products.append(product)
        
        # テーブル以外の構造も解析
        if len(products) < 5:
            products.extend(self.parse_jguitar_alternative_structure(soup, base_url))
        
        # 重複除去
        seen_names = set()
        unique_products = []
        for product in products:
            if product['name'] not in seen_names:
                seen_names.add(product['name'])
                unique_products.append(product)
        
        return unique_products[:15]  # 最大15件に制限
    
    def is_likely_jguitar_product_name(self, text):
        """J-Guitarの商品名らしいテキストかを判定"""
        if not text or len(text) < 10:
            return False
        
        # ノイズテキストを除外
        noise_patterns = [
            '詳細', 'detail', '価格', 'price', '在庫', 'stock', '送料', 'shipping',
            'ログイン', 'login', 'メニュー', 'menu', 'カート', 'cart', '検索', 'search',
            '年', '月', '日', 'お問い合わせ', 'contact', 'ページ', 'page'
        ]
        
        text_lower = text.lower()
        if any(noise in text_lower for noise in noise_patterns):
            return False
        
        # 商品名らしい特徴
        positive_indicators = [
            # ブランド名
            'yamaha', 'gibson', 'fender', 'martin', 'taylor', 'ibanez',
            'ramirez', 'hernandez', 'cordoba', 'godin', 'alhambra',
            '河野', '桜井', '黒澤', '中村', 'kohno', 'sakurai',
            
            # ギター関連用語
            'classical', 'flamenco', 'guitar', 'ギター', 'クラシック', 'フラメンコ',
            'nylon', 'ナイロン', 'cedar', 'spruce', 'rosewood', 'ebony',
            'セダー', 'スプルース', 'ローズウッド', 'エボニー',
            
            # 年代・モデル
            '19', '20', 'model', 'no.', '#', 'vintage', 'ヴィンテージ',
            
            # サイズ・仕様
            '650mm', '640mm', '630mm', 'scale', 'top', 'back', 'side'
        ]
        
        has_positive = any(indicator in text_lower for indicator in positive_indicators)
        
        # 長さとアルファベット・数字の組み合わせをチェック
        has_good_length = 10 <= len(text) <= 150
        has_alphanumeric = bool(re.search(r'[a-zA-Z]', text)) and bool(re.search(r'[\d]', text))
        
        return has_positive and has_good_length
    
    def find_price_in_cell_or_nearby(self, cell, row):
        """セルまたは近くのセルで価格を検索"""
        # 同じセル内を先に検索
        price = self.extract_price_from_text(cell.get_text())
        if price:
            return price
        
        # 同じ行の他のセルを検索
        cells = row.find_all(['td', 'th'])
        for other_cell in cells:
            price = self.extract_price_from_text(other_cell.get_text())
            if price:
                return price
        
        return None
    
    def parse_jguitar_alternative_structure(self, soup, base_url):
        """J-Guitarの代替構造解析"""
        products = []
        
        # div要素での商品情報検索
        divs = soup.find_all('div', class_=True)
        
        for div in divs:
            text = div.get_text(strip=True)
            
            if self.is_likely_jguitar_product_name(text):
                # 価格を周辺で検索
                price = None
                
                # 親要素や兄弟要素で価格を検索
                parent = div.parent
                if parent:
                    price = self.extract_price_from_text(parent.get_text())
                
                if not price:
                    # 次の兄弟要素を検索
                    next_sibling = div.find_next_sibling()
                    if next_sibling:
                        price = self.extract_price_from_text(next_sibling.get_text())
                
                if price:
                    product = self.create_product_info(
                        store='jguitar',
                        name=text,
                        price=price,
                        link=base_url,
                        store_name='J-Guitar'
                    )
                    
                    if self.is_valid_product(product):
                        products.append(product)
        
        return products
    
    def is_ikebe_product_link(self, href, text):
        """イケベ楽器店の商品リンク判定"""
        product_indicators = ['pid=', '/detail', 'ProductDetail', '/item/']
        exclude_indicators = [
            'javascript:', 'mailto:', '#', '/search', '/category', '/cart',
            '/login', '/register', '/help', '/contact', '/company', '/privacy',
            'facebook.com', 'twitter.com', 'instagram.com', 'youtube.com',
            'sort=', 'page=', 'pno=', 'img=', 'dpcnt=',
        ]
        
        href_lower = href.lower()
        for exclude in exclude_indicators:
            if exclude in href_lower:
                return False
        
        for indicator in product_indicators:
            if indicator in href_lower:
                return True
        
        if text and len(text) > 1:
            instrument_brands = ['yamaha', 'fender', 'gibson', 'martin', 'taylor', 'hernandez', 'yacopi', 'yairi']
            if any(brand in text.lower() for brand in instrument_brands):
                if href.startswith('/') or 'ikebe-gakki.com' in href:
                    return True
        
        return False
    
    def find_nearby_price(self, link_element):
        """リンク要素の近くにある価格情報を取得"""
        current = link_element.parent
        for _ in range(3):
            if current is None:
                break
            price_text = current.get_text()
            price_match = self.extract_price_from_text(price_text)
            if price_match:
                return price_match
            current = current.parent
        return None
    
    def extract_price_from_text(self, text):
        """テキストから価格を抽出"""
        price_patterns = [
            r'¥([^\s]+)',
            r'(\d{1,3}(?:,\d{3})+)円',
            r'価格[：:]?\s*¥?([^\s]+)',
            r'(\d{1,3}(?:,\d{3})+)(?=\s*\(税込\))',
            r'￥([^\s]+)',
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, text)
            if match:
                price_str = match.group(1).replace(',', '')
                # 数字以外の文字を除去
                clean_price = re.sub(r'[^\d]', '', price_str)
                if clean_price and clean_price.isdigit():
                    return f"¥{int(clean_price):,}"
        return None
    
    def create_product_info(self, store, name, price, link, store_name):
        """商品情報を作成"""
        product_id = f"{store}_{hash(name + link)}".replace('-', '')[:15]
        
        return {
            'id': product_id,
            'name': name.strip(),
            'price': price if price else "価格確認中",
            'link': link,
            'store': store,
            'store_name': store_name,
            'found_date': datetime.now().isoformat()
        }
    
    def is_valid_product(self, product):
        """有効な商品情報かチェック（価格必須版）"""
        if not product or not isinstance(product, dict):
            return False
        
        name = product.get('name', '').strip()
        if not name or len(name) < 5:
            return False
        
        link = product.get('link', '')
        if not link or not link.startswith('http'):
            return False
        
        # 価格が必須：「価格確認中」や空の場合は除外
        price = product.get('price', '').strip()
        if not price or price == "価格確認中":
            return False
        
        # 有効な価格形式かチェック
        price_pattern = re.compile(r'¥\s*[\d,]+|[\d,]+円')
        if not price_pattern.search(price):
            return False
        
        # より厳密なノイズテキスト除外
        noise_texts = [
            'more', '読み込み中', 'loading', '...', '詳細', 'detail',
            'もっと見る', 'view more', 'show more', '続きを見る',
            'next', 'prev', 'previous', '次へ', '前へ', 'ページ', 'page',
            'カート', 'cart', 'ログイン', 'login', 'menu', 'メニュー',
            'search', '検索', 'category', 'カテゴリ', 'home', 'ホーム',
            'top', 'トップ', 'back', '戻る', 'help', 'ヘルプ',
            'contact', 'お問い合わせ', 'unknown', '不明', 'n/a',
            'none', 'null', '送料', '出品', 'webshop', 'キャンペーン',
            '発送予定', '買い取り', '下取り', 'ポイント', '査定',
            '商品ピックアップ情報', 'pickup item', '検索該当件数',
            '全17件', '全件', '件数'
        ]
        
        name_lower = name.lower()
        for noise in noise_texts:
            if name_lower == noise or name_lower.startswith(noise + ' ') or noise in name_lower:
                return False
        
        # 短すぎる商品名を除外
        if len(name.replace(' ', '')) < 5:
            return False
        
        # 記号のみの商品名を除外
        if all(c in '.,;:!?()-[]{}/*+=・' for c in name.replace(' ', '')):
            return False
        
        return True
    
    def load_previous_data(self):
        """前回のデータを読み込み"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                self.logger.info("📄 初回実行のため、前回データなし")
                return {}
        except Exception as e:
            self.logger.error(f"データ読み込みエラー: {e}")
            return {}
    
    def save_data(self, all_products):
        """商品データを保存"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(all_products, f, indent=2, ensure_ascii=False)
            
            total_count = sum(len(products) for products in all_products.values())
            self.logger.info(f"💾 全サイトの商品データを保存: {total_count}件")
        except Exception as e:
            self.logger.error(f"データ保存エラー: {e}")
    
    def find_new_products(self, current_products, previous_products):
        """新商品を検出"""
        all_new_products = {}
        
        for store_key, current_store_products in current_products.items():
            previous_store_products = previous_products.get(store_key, [])
            previous_ids = {p['id'] for p in previous_store_products}
            
            new_products = [p for p in current_store_products if p['id'] not in previous_ids]
            
            if new_products:
                all_new_products[store_key] = new_products
        
        return all_new_products
    
    def filter_high_value_products(self, all_new_products):
        """10万円以上の商品のみをフィルタリング"""
        filtered_products = {}
        
        for store_key, products in all_new_products.items():
            high_value_products = [p for p in products if self.is_high_value_product(p)]
            if high_value_products:
                filtered_products[store_key] = high_value_products
        
        return filtered_products
    
    def detect_special_keywords(self, all_new_products):
        """特別なキーワードを検出"""
        special_products = []
        
        for store_key, products in all_new_products.items():
            for product in products:
                if self.has_special_keywords(product['name']):
                    special_products.append({
                        'store': self.stores[store_key]['name'],
                        'name': product['name'],
                        'price': product['price']
                    })
        
        return special_products
    
    def send_email(self, all_new_products):
        """新商品をメールで通知（10万円以上＆キーワード検出機能付き）"""
        try:
            email_config = self.config['email']
            
            if not all([email_config.get('sender_email'), email_config.get('sender_password'), email_config.get('recipient_email')]):
                self.logger.error("❌ メール設定が不完全です")
                return
            
            # 10万円以上の商品のみをフィルタリング
            filtered_products = self.filter_high_value_products(all_new_products)
            total_new = sum(len(products) for products in filtered_products.values())
            
            if total_new == 0:
                self.logger.info("📧 10万円以上の新商品がないため、メール送信をスキップ")
                return
            
            # 特別なキーワードの検出
            special_keyword_products = self.detect_special_keywords(filtered_products)
            
            subject = f"🎸 高価格新商品が{total_new}件見つかりました - 5サイト統合監視（毎日・10万円以上のみ） [GitHub Actions]"
            
            body = ""
            
            # 特別なキーワードが検出された場合は冒頭に記載
            if special_keyword_products:
                body += "🌟" * 50 + "\n"
                body += "🔥 【特別注目商品】ダブルトップ・ラティス構造の商品を発見！ 🔥\n"
                body += "🌟" * 50 + "\n\n"
                
                for special in special_keyword_products:
                    body += f"🏪 {special['store']}: {special['name']} ({special['price']})\n"
                
                body += "\n" + "=" * 60 + "\n\n"
            
            body += f"5つの楽器店サイトで高価格新商品 {total_new}件を検出しました！\n"
            body += f"（10万円以上の商品のみ・価格情報付き）\n\n"
            body += "=" * 60 + "\n\n"
            
            for store_key, new_products in filtered_products.items():
                store_name = self.stores[store_key]['name']
                body += f"🏪 【{store_name}】 新商品 {len(new_products)}件\n"
                body += "-" * 40 + "\n\n"
                
                for i, product in enumerate(new_products, 1):
                    price_value = self.extract_price_value(product['price'])
                    body += f"{i}. 📦 {product['name']}\n"
                    body += f"   💰 {product['price']} (¥{price_value:,})\n"
                    
                    # 特別なキーワードがある場合は強調
                    if self.has_special_keywords(product['name']):
                        body += f"   🌟 ダブルトップ/ラティス構造商品\n"
                    
                    body += f"   🔗 {product['link']}\n\n"
                
                body += "\n"
            
            body += "=" * 60 + "\n"
            body += f"実行時刻: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')} (UTC)\n"
            body += f"実行環境: GitHub Actions 5サイト統合監視（毎日・10万円以上・改良版）\n"
            body += f"対象サイト: イケベ楽器店、黒澤楽器店、島村楽器、QSic、J-Guitar\n"
            body += f"実行頻度: 毎日 日本時間8:00\n"
            body += f"価格制限: 10万円以上のみ通知"
            
            msg = MIMEMultipart()
            msg['From'] = email_config['sender_email']
            msg['To'] = email_config['recipient_email']
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
                server.starttls()
                server.login(email_config['sender_email'], email_config['sender_password'])
                server.send_message(msg)
            
            self.logger.info(f"📧 メール送信完了: {total_new}件の高価格新商品（10万円以上・改良版）")
            
            if special_keyword_products:
                self.logger.info(f"🌟 特別キーワード商品: {len(special_keyword_products)}件")
            
        except Exception as e:
            self.logger.error(f"メール送信エラー: {e}")
    
    def check_for_updates(self):
        """全サイトの商品更新をチェック"""
        self.logger.info("🔍 5サイト統合商品チェック開始（毎日・10万円以上・改良版）")
        
        current_products = self.get_all_products()
        
        if not any(current_products.values()):
            self.logger.warning("⚠️ 全サイトで商品データが取得できませんでした")
            return
        
        previous_products = self.load_previous_data()
        all_new_products = self.find_new_products(current_products, previous_products)
        
        if all_new_products:
            total_new = sum(len(products) for products in all_new_products.values())
            self.logger.info(f"🎉 5サイト合計で新商品を{total_new}件発見（価格付き）")
            
            # 10万円以上の商品のみをカウント
            filtered_products = self.filter_high_value_products(all_new_products)
            total_high_value = sum(len(products) for products in filtered_products.values())
            
            self.logger.info(f"💰 うち10万円以上の商品: {total_high_value}件")
            
            for store_key, new_products in all_new_products.items():
                store_name = self.stores[store_key]['name']
                high_value_count = len([p for p in new_products if self.is_high_value_product(p)])
                self.logger.info(f"  ➡️ {store_name}: {len(new_products)}件 (10万円以上: {high_value_count}件)")
                
                for product in new_products[:3]:
                    price_value = self.extract_price_value(product['price'])
                    emoji = "💰" if price_value >= 100000 else "💴"
                    self.logger.info(f"     {emoji} {product['name'][:50]}... ({product['price']})")
            
            self.send_email(all_new_products)
        else:
            self.logger.info("ℹ️ 5サイト全体で新商品はありませんでした")
        
        self.save_data(current_products)
        self.logger.info("✅ 5サイト統合商品チェック完了（毎日・10万円以上・改良版）")
        
        if os.getenv('GITHUB_ACTIONS'):
            total_current = sum(len(products) for products in current_products.values())
            total_new = sum(len(products) for products in all_new_products.values()) if all_new_products else 0
            total_high_value = sum(len(products) for products in self.filter_high_value_products(all_new_products).values()) if all_new_products else 0
            print(f"::notice title=5サイト統合監視完了（改良版）::総商品数: {total_current}, 新商品: {total_new}, 10万円以上: {total_high_value}")

def main():
    """メイン実行関数"""
    try:
        print("🚀 5サイト統合楽器店監視システム開始")
        print(f"実行時刻: {datetime.now()}")
        print(f"GitHub Actions環境: {bool(os.getenv('GITHUB_ACTIONS'))}")
        
        monitor = PriceRequiredMultiStoreMusicMonitor()
        print("✅ 監視システム初期化完了")
        
        monitor.check_for_updates()
        print("🎯 5サイト統合監視処理が正常に完了しました（毎日・10万円以上・改良版）")
        
    except Exception as e:
        import traceback
        error_msg = f"❌ 実行エラー: {e}"
        print(error_msg)
        print("詳細なエラー情報:")
        print(traceback.format_exc())
        
        # エラーログファイルを作成
        try:
            with open('error_log.txt', 'w', encoding='utf-8') as f:
                f.write(f"実行時刻: {datetime.now()}\n")
                f.write(f"エラー: {e}\n")
                f.write(f"詳細:\n{traceback.format_exc()}")
        except:
            pass
        
        sys.exit(1)

if __name__ == "__main__":
    main()
