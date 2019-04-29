## PubGate Telegram <-> ActivityPub bridge
Extension for [PubGate](https://github.com/autogestion/pubgate), federates Telegram channels and back

Requires PubGate >= 0.2.9
### Run
 - Create Telegram bot and invite it to broadcasting channels
 - Install PubGate
 - Install pg_telegram
 ```
 pip install git+https://github.com/autogestion/pubgate-telegram.git

```
 - Update conf.cfg with
```
EXTENSIONS = [..., "pg_telegram"]

# These example values won't work. You must get your own api_id and
# api_hash from https://my.telegram.org, under API Development.
TELEGRAM_API_ID = 12345
TELEGRAM_API_HASH = '0123456789abcdef0123456789abcdef'

TELEGRAM_BOT_TOKEN = "get from https://core.telegram.org/bots#6-botfather"

CHECK_BOXES_TIMEOUT = 3
```
 - run
```
python run_api.py

```


### Usage

#### Create bot
```
/user  POST
```
payload
```
{
	"username": "user",
	"password": "pass",
	"email": "admin@mail.com",                                     #optional
	"invite": "xyz",                                               #required if register by invite enabled
	"profile": {
		"type": "Service",
		"preferredUsername": "TelePub",
		"summary": "Broadcast from <a href='https://t.me/telapub' target='_blank'>Telegram channel",
	    "icon": {
	        "type": "Image",
	        "mediaType": "image/png",
	        "url": "https://cdn1.iconfinder.com/data/icons/blockchain-8/48/icon0008_decentralize-512.png"
	    }
	}
	"details": {
		"tgbot": {
			"channels": ["telapub"],
			"enable": true,
			"tags": ["telegram", "bridge"]                                #could be empty []
		}
	}
}
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
