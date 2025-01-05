WelcomeText = \
"""\
Hi **%(first_name)s**, send me a file to instantly generate file links.

**Commands:**
/privacy - Reply to file with the /link command to get download or stream link.
/log - Get bot's log file. (owner only)
/help - Show this message.
"""

FileLinksText = \
"""
**Download Link:**
`%(dl_link)s`
"""

MediaLinksText = \
"""
**Download Link:**
`%(dl_link)s`
**Stream Link:**
`%(stream_link)s`
"""

InvalidQueryText = \
"""
Query data mismatched.
"""

MessageNotExist = \
"""
File revoked or not exist.
"""

LinkRevokedText = \
"""
The link has been revoked. It may take some time for the changes to take effect.
"""

InvalidPayloadText = \
"""
Invalid payload.
"""

UserNotInAllowedList = \
"""
You are not allowed to use this bot.
"""
