Things to be careful of:

Cache for HF and Torch and Transformers must be set to /mnt/data

# 1. ASR -- 8001
tmux new -s asr
cd /mnt/data/asr-finetuning
source /mnt/data/asr-env/bin/activate 
python inference/asr_server.py

## 2. INDIC F5 TTS -- 8002
tmux new -s tts
docker exec -it xenodochial_payne bash (if stopped, docker start xenodochial_payne)

cd /mnt/data/tts
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
python app.py

# 3. INDIC TRANS 2 -- 8003
tmux new -s trans
cd /mnt/data/translation
source /mnt/data/translation/indictrans_env/bin/activate
python app.py

# 4. Surya OCR -- 8004
tmux new -s surya_ocr
cd /mnt/data/ocr-translation/backend
source /mnt/data/ocr-translation/backend/ocr_env310/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8004



# NGROK -- Export 8009
tmux new -s ngrok
ngrok http 8009

# Master Server -- 8009 (routes to all ports)
tmux new -s master
cd /mnt/data/chaitanya
source /mnt/data/asr-env/bin/activate
python master_server.py
