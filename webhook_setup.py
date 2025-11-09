import logging

async def setup_webhook(application, token, url):
    if not url:
        raise ValueError("RENDER_EXTERNAL_URL not set!")

    webhook_url = f"{url}/{token}"

    await application.bot.delete_webhook()
    await application.bot.set_webhook(webhook_url)

    logging.info("Webhook set to: " + webhook_url)
