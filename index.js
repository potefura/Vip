import PostalMime from 'postal-mime';

export default {
  async email(message, env, ctx) {
    const API_URL = "https://mail-apis.potefura.jp/api/receive";
    const AUTH_TOKEN = "potefuraz247";

    const to = message.to;
    const from = message.from;
    const subject = message.headers.get("subject") || "Sem assunto";
    const emailParsed = await PostalMime.parse(message.raw);

    const payload = {
      email: to,
      message: {
        from,
        subject,
        text: btoa(unescape(encodeURIComponent(emailParsed.html)))
      }
    };

    await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${AUTH_TOKEN}`
      },
      body: JSON.stringify(payload)
    });
  }
};
