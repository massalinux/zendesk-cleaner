### So you want to clean zendesk older tickets but don't want to upgrade to expensive pro plans to activate export?

Use this to free space from your Zendesk account and keep a local copy of the ticket for bureaucratic reasons

## How to use it

- get your api token from `https://YOURSUBDOMAIN.zendesk.com/admin/apps-integrations/apis/zendesk-api/settings/tokens/`
- clone the repo
- cd into project
- make venv `python -m venv venv`
- source into venv `source venv/bin/activate`
- install requirements `pip install -r requirements.txt`
- create a .env from .env.example `cp .env.example .env` and **set your envs**
- start the script and leave it running  `python main.py`



## What you will get
The script create a folder for each ticket with a json of the whole conversation and will download each attachment and zip it, finally will delete the ticket from your zendesk account.

```bash
data/
├── 13668
│   ├── 13668-ticket.json
│   └── ?name=camici.docx.zip
├── 13669
│   └── 13669-ticket.json
├── 13671
│   └── 13671-ticket.json
├── 13672
│   ├── 13672-ticket.json
│   ├── ?name=S16102611210.pdf.zip
│   └── ?name=S16102611220.pdf.zip
├── 13673
│   └── 13673-ticket.json
```

### [Optional] Do you use PM2? 

If you use pm2 in your server here the ecosystem.config.json

```json
{
  "apps": [
    {
      "name": "zendesk-cleaner",
      "script": "main.py",
      "args": [],
      "exec_mode": "fork",
      "instances": "1",
      "wait_ready": true,
      "autorestart": true,
      "restart_delay": 20000,
      "max_restarts": 5,
      "interpreter": "venv/bin/python"
    }
  ]
}
```

then

`pm2 start ecosystem.config.js`




