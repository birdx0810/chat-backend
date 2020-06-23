curl -v -X POST https://api.line.me/v2/bot/richmenu \
-H 'Authorization: Bearer {LzbETiey6TxN3M/mJI2YZiQSGQmeH2NxTOCSu+GyVUOQSCHWP1fvQPJL9Cno0hvxxQsITuT0qe44FN0J9r2EBDn0tN01lPpqQe5pzOT1PZF3uXbEhekSkzAmvi5LDzlqc36ejUbZFIvE8zvKAI0TPgdB04t89/1O/w1cDnyilFU=}' \
-H 'Content-Type: application/json' \
-d \
'{
    "size": {
      "width": 2500,
      "height": 843
    },
    "selected": false,
    "name": "rich_menu",
    "chatBarText": "選單",
    "areas": [
      {
        "bounds": {
          "x": 0,
          "y": 0,
          "width": 1250,
          "height": 843
        },
        "action": {
          "type": "uri",
          "label": "手環使用手冊",
          "uri": "http://bit.ly/nckumb"
        }
      },
      {
        "bounds": {
          "x": 1250,
          "y": 0,
          "width": 1250,
          "height": 843
        },
        "action": {
          "type": "message",
          "label": "客服專線",
          "text": "/qa"
        }
      }
    ]
}'