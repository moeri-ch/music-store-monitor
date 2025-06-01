#!/usr/bin/env python3
"""
価格必須版5つの楽器店サイト統合監視プログラム (GitHub Actions対応・改良版)
週1回実行・価格情報付き商品のみ抽出
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
            self.logger.info("🚀 GitHub Actions で5サイト統合楽器店監視を開始（週1回・価格必須版・改良版）")
        else:
            self.logger.info("🚀 ローカル環境で5サイト統合楽器店監視を開始")
    
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
            return self.parse_jguitar_products_fixed(soup, store_info['base_url'])
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
    
    def parse_jguitar_products_fixed(self, soup, base_url):
        """J-Guitarの改良版商品解析（価格抽出強化）"""
        products = []
        text_content = soup.get_text()
        
        # テキストを行分割
        lines = [line.strip() for line in text_content.split('\n') if line.strip()]
        
        # より緩い価格パターンを定義
        price_patterns = [
            r'(\d{1,3}(?:,\d{3})+)円',
            r'¥\s*(\d{1,3}(?:,\d{3})+)',
            r'価格[：:\s]*(\d{1,3}(?:,\d{3})+)',
            r'(\d{1,3}(?:,\d{3})+)\s*円\s*\(',
            r'(\d{2,3},\d{3})(?:\s|$)',  # より緩いパターン
            r'(\d{6,})(?:\s|$)',         # 6桁以上の数字
        ]
        
        # 商品候補をより広く検索
        brand_keywords = [
            'ホセ・ラミレス', 'ラミレス', 'Ramirez', 'RAMIREZ',
            'ホアン・エルナンデス', 'エルナンデス', 'Hernandez', 'HERNANDEZ',
            '桜井', 'Sakurai', 'YAMAHA', 'Gibson', 'GIBSON', 'Ibanez', 'IBANEZ',
            'Godin', 'GODIN', 'Cordoba', 'CORDOBA', 'Esteve', 'ESTEVE',
            '河野', 'Kohno', '中村', 'Nakamura', '黒澤', 'Kurosawa',
            'Francisco', 'Antonio', 'Sanchez', 'Conde', 'Hermanos',
            'アントニオ', 'サンチェス', 'コンデ', 'エルマノス'
        ]
        
        guitar_keywords = [
            'クラシックギター', 'フラメンコギター', 'エレガット', 'ナイロン',
            '650mm', '640mm', 'セダー', 'ローズウッド', 'スプルース',
            'Classical', 'Flamenco', 'Guitar', 'Nylon'
        ]
        
        year_pattern = re.compile(r'(19|20)\d{2}年')
        
        # 価格情報を先に全て抽出
        price_lines = {}
        for i, line in enumerate(lines):
            for pattern in price_patterns:
                price_match = re.search(pattern, line)
                if price_match:
                    try:
                        price_num = int(price_match.group(1).replace(',', ''))
                        # 楽器として妥当な価格範囲
                        if 5000 <= price_num <= 10000000:
                            price_lines[i] = f"¥{price_match.group(1)}"
                    except:
                        pass
        
        # 商品名候補を検索
        product_candidates = []
        
        for i, line in enumerate(lines):
            is_product_line = False
            
            # 長さチェック（短すぎる・長すぎる行を除外）
            if len(line) < 10 or len(line) > 200:
                continue
            
            # ブランド名チェック
            for brand in brand_keywords:
                if brand in line:
                    is_product_line = True
                    break
            
            # 年製チェック
            if year_pattern.search(line):
                is_product_line = True
            
            # ギター関連キーワードチェック
            if any(keyword in line for keyword in guitar_keywords):
                is_product_line = True
            
            # モデル番号らしきパターンチェック
            model_patterns = [
                r'[A-Z]{2,}-\d+',    # CG-142, GC-7など
                r'No\.\d+',         # No.30など
                r'Model\s+\d+',     # Model 128など
            ]
            
            for pattern in model_patterns:
                if re.search(pattern, line):
                    is_product_line = True
                    break
            
            if is_product_line:
                # ノイズ行を除外
                noise_patterns = [
                    '発送予定', 'キャンペーン', 'ポイント', '買い取り', '下取り', 
                    'ログイン', 'クレジット', '分割', '無金利', '送料', '在庫', 
                    '入荷', '予約', '検索', 'カテゴリ', 'メニュー', 'ナビ'
                ]
                
                if not any(noise in line for noise in noise_patterns):
                    product_candidates.append((i, line))
        
        # 商品候補と価格の組み合わせを試行
        for line_num, product_name in product_candidates:
            # この商品候補の前後10行で価格を探索
            found_price = None
            
            for price_line_num, price in price_lines.items():
                if abs(price_line_num - line_num) <= 10:
                    found_price = price
                    break
            
            # 価格が見つからない場合はスキップ
            if not found_price:
                continue
            
            product = self.create_product_info(
                store='jguitar',
                name=product_name,
                price=found_price,
                link=base_url,
                store_name='J-Guitar'
            )
            
            if self.is_valid_product(product):
                products.append(product)
        
        # 重複除去
        seen_names = set()
        unique_products = []
        for product in products:
            if product['name'] not in seen_names:
                seen_names.add(product['name'])
                unique_products.append(product)
        
        return unique_products[:15]  # 最大15件に制限
    
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
            r'¥([\d,]+)',
            r'(\d{1,3}(?:,\d{3})+)円',
            r'価格[：:]?\s*¥?([\d,]+)',
            r'(\d{1,3}(?:,\d{3})+)(?=\s*\(税込\))',
            r'￥([\d,]+)',
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, text)
            if match:
                return f"¥{match.group(1)}"
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
    
    def send_email(self, all_new_products):
        """新商品をメールで通知"""
        try:
            email_config = self.config['email']
            
            if not all([email_config.get('sender_email'), email_config.get('sender_password'), email_config.get('recipient_email')]):
                self.logger.error("❌ メール設定が不完全です")
                return
            
            total_new = sum(len(products) for products in all_new_products.values())
            
            if total_new == 0:
                self.logger.info("📧 新商品がないため、メール送信をスキップ")
                return
            
            subject = f"🎸 新商品が{total_new}件見つかりました - 5サイト統合監視（週1回・価格付きのみ） [GitHub Actions]"
            
            body = f"5つの楽器店サイトで新商品 {total_new}件を検出しました！\n"
            body += f"（価格情報が取得できた商品のみ）\n\n"
            body += "=" * 60 + "\n\n"
            
            for store_key, new_products in all_new_products.items():
                store_name = self.stores[store_key]['name']
                body += f"🏪 【{store_name}】 新商品 {len(new_products)}件\n"
                body += "-" * 40 + "\n\n"
                
                for i, product in enumerate(new_products, 1):
                    body += f"{i}. 📦 {product['name']}\n"
                    body += f"   💰 {product['price']}\n"
                    body += f"   🔗 {product['link']}\n\n"
                
                body += "\n"
            
            body += "=" * 60 + "\n"
            body += f"実行時刻: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')} (UTC)\n"
            body += f"実行環境: GitHub Actions 5サイト統合監視（週1回・価格付き商品のみ・改良版）\n"
            body += f"対象サイト: イケベ楽器店、黒澤楽器店、島村楽器、QSic、J-Guitar\n"
            body += f"実行頻度: 毎週土曜日 日本時間9:00"
            
            msg = MIMEMultipart()
            msg['From'] = email_config['sender_email']
            msg['To'] = email_config['recipient_email']
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
                server.starttls()
                server.login(email_config['sender_email'], email_config['sender_password'])
                server.send_message(msg)
            
            self.logger.info(f"📧 メール送信完了: {total_new}件の新商品（5サイト統合・改良版）")
            
        except Exception as e:
            self.logger.error(f"メール送信エラー: {e}")
    
    def check_for_updates(self):
        """全サイトの商品更新をチェック"""
        self.logger.info("🔍 5サイト統合商品チェック開始（価格必須版・改良版）")
        
        current_products = self.get_all_products()
        
        if not any(current_products.values()):
            self.logger.warning("⚠️ 全サイトで商品データが取得できませんでした")
            return
        
        previous_products = self.load_previous_data()
        all_new_products = self.find_new_products(current_products, previous_products)
        
        if all_new_products:
            total_new = sum(len(products) for products in all_new_products.values())
            self.logger.info(f"🎉 5サイト合計で新商品を{total_new}件発見（価格付き）")
            
            for store_key, new_products in all_new_products.items():
                store_name = self.stores[store_key]['name']
                self.logger.info(f"  ➡️ {store_name}: {len(new_products)}件")
                for product in new_products[:3]:
                    self.logger.info(f"     - {product['name'][:50]}... ({product['price']})")
            
            self.send_email(all_new_products)
        else:
            self.logger.info("ℹ️ 5サイト全体で新商品はありませんでした")
        
        self.save_data(current_products)
        self.logger.info("✅ 5サイト統合商品チェック完了（価格必須版・改良版）")
        
        if os.getenv('GITHUB_ACTIONS'):
            total_current = sum(len(products) for products in current_products.values())
            total_new = sum(len(products) for products in all_new_products.values()) if all_new_products else 0
            print(f"::notice title=5サイト統合監視完了（改良版）::総商品数: {total_current}, 新商品: {total_new}")

def main():
    """メイン実行関数"""
    try:
        print("🚀 5サイト統合楽器店監視システム開始")
        print(f"実行時刻: {datetime.now()}")
        print(f"GitHub Actions環境: {bool(os.getenv('GITHUB_ACTIONS'))}")
        
        monitor = PriceRequiredMultiStoreMusicMonitor()
        print("✅ 監視システム初期化完了")
        
        monitor.check_for_updates()
        print("🎯 5サイト統合監視処理が正常に完了しました（価格必須版・改良版）")
        
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
