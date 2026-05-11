import json
import asyncio
from main import AuthBypass 

def handler(event, context):
    # POST以外のアクセスを拒否
    if event.get('httpMethod') != 'POST':
        return {'statusCode': 405, 'body': 'Method Not Allowed'}

    try:
        # フロントエンドから送られてきたデータ(JSON)を解析
        payload = json.loads(event.get('body', '{}'))
        
        token = payload.get('token')
        config = {
            'solver_type': payload.get('solverType'),
            'gemini_api_key': payload.get('solverApiKey'),
            '2captcha_api_key': payload.get('solverApiKey'),
            'capmonster_api_key': payload.get('solverApiKey'),
            'capsolver_api_key': payload.get('solverApiKey')
        }

        # Pythonのクラスを呼び出し
        bypass = AuthBypass(token, config)

        # 非同期処理を実行するための設定
        loop = asyncio.get_event_loop()
        
        # クラス内の bypass_auth メソッドを実行
        result = loop.run_until_complete(bypass.bypass_auth(
            payload.get('serverId'),
            payload.get('messageId'),
            payload.get('method'),
            channel_id=payload.get('channelId'),
            emoji=payload.get('emoji'),
            button_text=payload.get('buttonText'),
            first_button_text=payload.get('firstButtonText'),
            input_text=payload.get('inputText'),
            answer_button_text=payload.get('answerButtonText')
        ))

        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'message': str(result)
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }
