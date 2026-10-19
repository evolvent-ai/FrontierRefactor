Quick Start
===========

Welcome to Hydrogram! This guide will help you set up and run your first Telegram bot or client application in minutes.

What is Hydrogram?
------------------

Hydrogram is a modern, elegant Python framework that allows you to interact with the Telegram API. With Hydrogram, you can:

- Create Telegram bots with advanced features
- Build user clients (userbot)
- Access and manage your Telegram account programmatically
- Automate Telegram-related tasks
- Handle updates and respond to messages

Let's get started with a simple example:

Getting Started
---------------

1. **Install Hydrogram** with ``pip3 install -U hydrogram``.

2. **Obtain your API credentials** from Telegram:

   - Go to https://my.telegram.org/apps and log in with your phone number
   - Create a new application to get your ``api_id`` and ``api_hash``

.. note::

    Make sure you understand and abide by Telegram's terms of service and API usage rules explained at https://core.telegram.org/api/obtaining_api_id.

3. **Create your first script** by opening your favorite text editor and pasting the following code:

    .. code-block:: python

        import asyncio
        from hydrogram import Client

        # Replace these with your own values
        api_id = 12345
        api_hash = "0123456789abcdef0123456789abcdef"


        async def main():
            # Create a new client instance
            async with Client("my_account", api_id, api_hash) as app:
                # Send a message to yourself
                await app.send_message("me", "Greetings from **Hydrogram**!")

                # Get information about yourself
                me = await app.get_me()
                print(f"Successfully logged in as {me.first_name} ({me.id})")


        asyncio.run(main())

4. **Replace** the placeholder ``api_id`` and ``api_hash`` values with your own.

5. **Save the file** as ``hello.py``.

6. **Run the script** with ``python3 hello.py``

7. **Log in to your account** by following the prompts. You'll only need to do this once.

8. **Watch Hydrogram in action** as it sends a message to your Saved Messages.

What's Next?
------------

This was just a brief introduction to get you started quickly. Hydrogram offers many more powerful features for building Telegram applications.

- Learn about different ways to :doc:`../start/invoking` from the API
- Explore how to :doc:`../start/updates` from Telegram
- Check out complete :doc:`../start/examples/index` to see what's possible

Join our `community`_ on Telegram for support and updates.

.. _community: https://t.me/HydrogramNews
