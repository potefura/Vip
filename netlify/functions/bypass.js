// netlify/functions/bypass.js
const { AuthBypass } = require('../../index');

exports.handler = async (event) => {
    if (event.httpMethod !== 'POST') {
        return { statusCode: 405, body: 'Method Not Allowed' };
    }
    
    try {
        const payload = JSON.parse(event.body);
        
        const config = {
            solver_type: payload.solverType,
            gemini_api_key: payload.solverApiKey,
            '2captcha_api_key': payload.solverApiKey,
            'capmonster_api_key': payload.solverApiKey,
            'capsolver_api_key': payload.solverApiKey
        };
        
        const bypass = new AuthBypass(payload.token, config);
        
        const result = await bypass.bypass_auth(
            payload.serverId,
            payload.messageId,
            payload.method,
            {
                channel_id: payload.channelId,
                emoji: payload.emoji,
                button_text: payload.buttonText,
                first_button_text: payload.firstButtonText,
                input_text: payload.inputText,
                answer_button_text: payload.answerButtonText
            }
        );
        
        return {
            statusCode: 200,
            body: JSON.stringify({
                success: true,
                message: result
            })
        };
    } catch (error) {
        return {
            statusCode: 500,
            body: JSON.stringify({
                success: false,
                error: error.message
            })
        };
    }
};
