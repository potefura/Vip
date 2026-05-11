# discord_auth_bypass.py
import discord
import asyncio
import aiohttp
import re
import base64
from io import BytesIO
from PIL import Image
import google.generativeai as genai

class AuthBypass:
    def __init__(self, token, config):
        self.token = token
        self.client = discord.Client()
        self.config = config  # solver settings, api keys
        
    async def solve_captcha_image(self, image_url):
        """画像CAPTCHAを解析"""
        solver_type = self.config.get('solver_type')
        
        if solver_type == 'gemini':
            return await self._solve_with_gemini(image_url)
        elif solver_type == '2captcha':
            return await self._solve_with_2captcha(image_url)
        elif solver_type == 'capmonster':
            return await self._solve_with_capmonster(image_url)
        elif solver_type == 'capsolver':
            return await self._solve_with_capsolver(image_url)
        elif solver_type == 'custom':
            return await self._solve_with_custom(image_url)
    
    async def _solve_with_gemini(self, image_url):
        """Gemini APIで画像内の数字を読み取る"""
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                img_data = await resp.read()
        
        genai.configure(api_key=self.config['gemini_api_key'])
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        img = Image.open(BytesIO(img_data))
        
        prompt = """この画像に描かれている4桁の数字を読み取ってください。
        斜線で消されている数字は無視して、はっきり見える数字だけを左から順に答えてください。
        数字だけを返してください。例: 4386"""
        
        response = model.generate_content([prompt, img])
        result = re.sub(r'[^0-9]', '', response.text)
        return result
    
    async def _solve_with_2captcha(self, image_url):
        """2captcha APIを使用"""
        api_key = self.config['2captcha_api_key']
        
        async with aiohttp.ClientSession() as session:
            # 画像ダウンロード
            async with session.get(image_url) as resp:
                img_data = await resp.read()
            
            img_base64 = base64.b64encode(img_data).decode()
            
            # タスク送信
            submit_url = f'http://2captcha.com/in.php'
            params = {
                'key': api_key,
                'method': 'base64',
                'body': img_base64,
                'json': 1,
                'numeric': 1,  # 数字のみ
                'min_len': 4,
                'max_len': 4
            }
            
            async with session.post(submit_url, data=params) as resp:
                result = await resp.json()
                captcha_id = result['request']
            
            # 結果取得（最大120秒待機）
            result_url = f'http://2captcha.com/res.php'
            for _ in range(24):
                await asyncio.sleep(5)
                async with session.get(result_url, params={
                    'key': api_key,
                    'action': 'get',
                    'id': captcha_id,
                    'json': 1
                }) as resp:
                    result = await resp.json()
                    if result['status'] == 1:
                        return result['request']
        
        return None
    
    async def _solve_with_capmonster(self, image_url):
        """CapMonster Cloud API"""
        api_key = self.config['capmonster_api_key']
        
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                img_data = await resp.read()
            
            img_base64 = base64.b64encode(img_data).decode()
            
            # タスク作成
            create_task = {
                'clientKey': api_key,
                'task': {
                    'type': 'ImageToTextTask',
                    'body': img_base64,
                    'numeric': 1,
                    'minLength': 4,
                    'maxLength': 4
                }
            }
            
            async with session.post('https://api.capmonster.cloud/createTask', json=create_task) as resp:
                result = await resp.json()
                task_id = result['taskId']
            
            # 結果取得
            for _ in range(24):
                await asyncio.sleep(5)
                async with session.post('https://api.capmonster.cloud/getTaskResult', json={
                    'clientKey': api_key,
                    'taskId': task_id
                }) as resp:
                    result = await resp.json()
                    if result['status'] == 'ready':
                        return result['solution']['text']
        
        return None
    
    async def _solve_with_capsolver(self, image_url):
        """CapSolver API"""
        api_key = self.config['capsolver_api_key']
        
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                img_data = await resp.read()
            
            img_base64 = base64.b64encode(img_data).decode()
            
            payload = {
                'clientKey': api_key,
                'task': {
                    'type': 'ImageToTextTask',
                    'body': img_base64,
                    'module': 'common',
                    'score': 0.8
                }
            }
            
            async with session.post('https://api.capsolver.com/createTask', json=payload) as resp:
                result = await resp.json()
                task_id = result['taskId']
            
            for _ in range(24):
                await asyncio.sleep(3)
                async with session.post('https://api.capsolver.com/getTaskResult', json={
                    'clientKey': api_key,
                    'taskId': task_id
                }) as resp:
                    result = await resp.json()
                    if result['status'] == 'ready':
                        return result['solution']['text']
        
        return None
    
    async def _solve_with_custom(self, image_url):
        """カスタム画像認識（フロントエンドのPython実装）"""
        # 独自のOCRロジック（軽量版）
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                img_data = await resp.read()
        
        img = Image.open(BytesIO(img_data))
        # ここにカスタムOCRロジック
        # Tesseract OCRとか使える
        import pytesseract
        text = pytesseract.image_to_string(img, config='--psm 7 digits')
        return re.sub(r'[^0-9]', '', text)
    
    async def bypass_auth(self, server_id, message_id, method, **kwargs):
        """認証をバイパス"""
        guild = self.client.get_guild(int(server_id))
        
        if method == 'reaction':
            channel = guild.get_channel(int(kwargs['channel_id']))
            message = await channel.fetch_message(int(message_id))
            emoji = kwargs['emoji']  # '👋' or emoji_id
            await message.add_reaction(emoji)
            return f"リアクション {emoji} を追加しました"
        
        elif method == 'button':
            # Discordのボタンをクリック
            channel = guild.get_channel(int(kwargs['channel_id']))
            message = await channel.fetch_message(int(message_id))
            
            # ボタンのcustom_idを探す
            for component in message.components:
                for button in component.children:
                    if button.label == kwargs['button_text']:
                        await button.click()
                        return f"ボタン '{kwargs['button_text']}' をクリックしました"
        
        elif method == 'number_input':
            # ボタンクリック後、フォームに入力
            channel = guild.get_channel(int(kwargs['channel_id']))
            message = await channel.fetch_message(int(message_id))
            
            # 最初のボタンクリック
            for component in message.components:
                for button in component.children:
                    if button.label == kwargs['first_button_text']:
                        await button.click()
                        break
            
            await asyncio.sleep(2)  # フォームが表示されるまで待つ
            
            # フォームに入力
            await channel.send(kwargs['input_text'])
            return f"'{kwargs['input_text']}' を入力しました"
        
        elif method == 'image_captcha':
            channel = guild.get_channel(int(kwargs['channel_id']))
            message = await channel.fetch_message(int(message_id))
            
            # 最初のボタンクリック
            for component in message.components:
                for button in component.children:
                    if button.label == kwargs['button_text']:
                        await button.click()
                        break
            
            await asyncio.sleep(3)  # 画像が送られるまで待つ
            
            # 最新メッセージから画像取得
            messages = [msg async for msg in channel.history(limit=1)]
            latest_msg = messages[0]
            
            if latest_msg.attachments:
                image_url = latest_msg.attachments[0].url
                solution = await self.solve_captcha_image(image_url)
                
                # 2番目のボタンクリック前に解答準備
                await asyncio.sleep(1)
                
                # 答えを入力ボタンをクリック
                for component in latest_msg.components:
                    for button in component.children:
                        if kwargs.get('answer_button_text') in button.label:
                            await button.click()
                            break
                
                await asyncio.sleep(2)
                
                # 解答を送信
                await channel.send(solution)
                return f"CAPTCHA解答: {solution} を送信しました"
        
        elif method == 'math':
            channel = guild.get_channel(int(kwargs['channel_id']))
            message = await channel.fetch_message(int(message_id))
            
            # 認証ボタンクリック
            for component in message.components:
                for button in component.children:
                    if button.label == kwargs['button_text']:
                        await button.click()
                        break
            
            await asyncio.sleep(2)
            
            # フォームから計算式を取得して解く
            messages = [msg async for msg in channel.history(limit=1)]
            latest_msg = messages[0]
            
            # "5×8の答えは?" みたいなテキストから計算
            text = latest_msg.content
            match = re.search(r'(\d+)\s*[×x]\s*(\d+)', text)
            if match:
                num1, num2 = int(match.group(1)), int(match.group(2))
                answer = num1 * num2
                
                # 答えを送信
                await asyncio.sleep(1)
                await channel.send(str(answer))
                return f"計算結果: {answer} を送信しました"
        
        return "認証失敗"
    
    def run(self):
        self.client.run(self.token, bot=False)
