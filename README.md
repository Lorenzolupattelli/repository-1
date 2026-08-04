# repository-1 — Integrazione Meta Marketing API (Facebook / Instagram Ads)

Integrazione in **Python** per collegare Claude Code al tuo **ad account Meta**
(Facebook / Instagram). Permette di **leggere gli insight** (spese, click,
impression, ROAS…) e di **creare/gestire campagne** tramite l'SDK ufficiale
[`facebook-business`](https://github.com/facebook/facebook-python-business-sdk).

## Cosa ti serve

Dato che hai già creato l'app e il collegamento API, ti servono questi valori:

| Valore | Dove trovarlo |
|---|---|
| **Access token** | Graph API Explorer o System User su business.facebook.com |
| **Ad Account ID** | Gestione Inserzioni → in alto (formato `act_1234567890`) |
| **App ID / App Secret** | developers.facebook.com → la tua app → Impostazioni |

Permessi necessari sul token: `ads_read` (lettura) e `ads_management` (scrittura).

## Installazione

```bash
# 1. Crea un ambiente virtuale e installa le dipendenze
python -m venv .venv
source .venv/bin/activate        # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Configura le credenziali
cp .env.example .env
# poi apri .env e incolla i tuoi valori reali
```

> ⚠️ **Sicurezza:** il file `.env` contiene segreti ed è già escluso da git
> (`.gitignore`). Non committarlo e non condividerlo mai.

## Uso

### 1. Verifica il collegamento
```bash
python scripts/check_connection.py
```
Se il token è valido, stampa nome, valuta e stato dell'account. **Inizia da qui.**

### 2. Leggi gli insight
```bash
python scripts/read_insights.py                 # ultimi 30 giorni, per campagna
python scripts/read_insights.py last_7d         # ultimi 7 giorni
python scripts/read_insights.py this_month adset # questo mese, per adset
```

### 3. Crea una campagna (in PAUSED, per sicurezza)
```bash
python scripts/create_campaign.py "Nome campagna" OUTCOME_TRAFFIC
```
La campagna viene creata **in pausa**: non spende nulla finché non la attivi tu.

## Struttura del progetto

```
metaads/
  config.py    # carica e valida le credenziali da .env
  client.py    # MetaAdsClient: lettura insight + gestione campagne
scripts/
  check_connection.py   # verifica il token/collegamento
  read_insights.py      # scarica gli insight
  create_campaign.py    # crea una campagna di test (PAUSED)
```

## Uso da codice

```python
from metaads import MetaAdsClient

client = MetaAdsClient()
print(client.get_account_info())
print(client.get_insights(level="campaign", date_preset="last_7d"))
```
