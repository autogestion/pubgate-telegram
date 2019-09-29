## PubGate Telegram <-> ActivityPub bridge
Extension for [PubGate](https://github.com/autogestion/pubgate), federates Telegram channels and back
                            
Requires PubGate >= 0.2.19
## Deploy
Create Telegram bot and invite it to channels going to be bridged
###### Install Docker + Docker Compose
#### Shell
```
git clone https://github.com/autogestion/pubgate.git
cp -r config/extensions_sample_conf.cfg config/conf.cfg
```
##### Edit config/conf.cfg to change setup of your instance, next values should be added
```
EXTENSIONS = [..., "pg_telegram"]
# These example values won't work. You must get your own api_id and
# api_hash from https://my.telegram.org, under API Development.
TELEGRAM_API_ID = 12345
TELEGRAM_API_HASH = '0123456789abcdef0123456789abcdef'
TELEGRAM_BOT_TOKEN = "get from https://core.telegram.org/bots#6-botfather"
CHECK_BOXES_TIMEOUT = 3
```
This will connect Telegram bot to PubGate server. To connect it to Fediverse, setup PubGate AP account.
Account could be created on deploy by adding next value to config/conf.cfg or later via API (described below)
```
USER_ON_DEPLOY = """{
    "username": "user",
    "password": "pass",
    "email": "admin@mail.com",                                          #optional    
    "profile": {
        "type": "Service",                                              #could be set as "Person"    
        "name": "TelePub",
        "summary": "Broadcast from <a href='https://t.me/telapub' target='_blank'>Telegram channel</a>",
        "icon": {
            "type": "Image",
            "mediaType": "image/png",
            "url": "https://cdn1.iconfinder.com/data/icons/blockchain-8/48/icon0008_decentralize-512.png"
        }
    },
    "details": {
        "tgbot": {
            "channels": ["telapub"],                                    #list of channel names, as they defined in Telegram
            "enable": true,
            "tags": ["telegram", "bridge"]                              #could be empty []
        }
    }
}"""
```
##### Edit requirements/extensions.txt by adding next row
```
git+https://github.com/autogestion/pubgate-telegram.git
```

Then, instance could be started
```
domain=put-your-domain-here.com docker-compose up -d
```

### Usage

- To get updates from Telegram channels (where Telegram bot was added) just follow PubGate account from any other instance
- To send updates to Telegram, make PubGate account follow accounts from other instances (via UI or API, Endpoint and payload are described in postman collection in [Pubgate repo](https://github.com/autogestion/pubgate/blob/master/pubgate.postman_collection.json)

#### Bot Creation via API
```
/user  POST
```
payload 
```
Same as used for USER_ON_DEPLOY value, comments should be stripped
```

##### Restart app after adding new bot or updating old one

#### Disable/Update bot
```
/<username>  PATCH   (auth required)
```
payload
```
{
    "details": {
        "tgbot": {
            "channels": ["telapub"],                                      #change to update channel's list
            "enable": false,                                              #"enable": true to re-enable
            "tags": ["telegram", "bridge"]                                 #could be empty []
        }
    }
}
```
