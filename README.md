<h1 align="center">
  Semester 6 — Team VONK3_Sonic
  <br>
    Sonic Portaal: Inzicht in Biodiversiteit van Rotterdam
</h1>
<p align="center">
  <img src="sonic_hedg_banner.webp" alt="Sonic Hedgehog Banner" height="250">
</p>  

## About
__JA de naam "Sonic Portaal" is nog een placeholder...__  
Sonic Portaal is een webapplicatie die inzicht geeft in de biodiversiteit van verschillende wijken in Rotterdam.   
Dit gebeurt op basis van data van tien verschillende biodiversiteitsindicatoren, zoals planten en dieren.   
Daarnaast kun je in het portaal specifieke tijdsperiodes selecteren om te zien hoe de biodiversiteit er op dat moment uitzag.  
Met behulp van \*\*AI\*\* wordt bovendien een trendanalyse uitgevoerd op basis van historische gegevens,  
waardoor je kunt zien hoe de biodiversiteit zich in bepaalde wijken ontwikkelt.
- Git is opgedeeld in `.\frontend` en `.\backend` applicatie.
- Kan beide starten met Docker -> [HELP](#docker-build-guide)  
*__maar__ kan ook simpel met npm install als je nodejs geinstaleerd hebt.*

<br>

## Tech-stack (voor nu...)

- Backend: __Express.js__
    - Regelt communicatie met de __Postgres__ database
- Frontend: __React__
    - UI stuff & dynamische content
    - __Leaflet.js__ voor kaart manipulatie 


<br>


## Docker build guide

1. run `docker compose up --build ` 
Dit bouwt de backend en frontend dokcer containers 

__Als geen nodejs hebt geinstalleerd volg dit zodat de modules ook lokaal(host) aanwezig zijn__
2. Nu moet je de node_modules kopieren zodat de host(jij buiten docker) ook toegang krijgt tot de modules  
__doe dit in de locatie root folder van ./frontend IN ROOT OF ADMINISTRATOR MODE__  
-  `docker cp $FRONTEND CONTAINER NAME/ID$:/frontend_app/node_modules .`


# FAQ
1. Hoe importeer je nieuwe libs/modules (__Als je geen nodejs hebt geinstaleerd!!!__)?  
- Instaleer ze eerst in de docker container met  
`docker exec -it $CONTAINER_NAME$ bash`  
Nu zijn ze toegevoegd aan de package.json
  
- stop alleen de frontend container  
`docker compose stop $CONTAINER_NAME$`

__verwijder \node_modules, want je gaat gaat de nieuwe over copieeren__

- start alleen de frontend container  
`docker compose up $CONTAINER_NAME$`  
met `-d` for in background

- copy all node_modules zodat je intelisense krijgt   
(of sla deze stap over en doe npm install in host  
(als je Nodejs hebt geinstaleerd...))  
__Run the following command on host(outside docker) in the /frontend__  
__With sudo or administrator cmd__ 

```
 docker cp $CONTAINER_NAME$:./frontend/node_modules .
```

ps verander frontend -> backend als je daar een module wilt toevoegen en pas compose.yaml aan :thinking:
