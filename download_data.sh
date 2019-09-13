# Downloads the data for one year, year given as a command line argument
curl -g -G "https://www.jarviwiki.fi/w/api.php"\
 --data-urlencode "action=ask"\
 --data-urlencode "query=[[Havainto::>0]][[Tyyppi::Levätilanne]]"\
"[[Seuranta::Valtakunnallinen leväseuranta]][[Vuosi::"$1"]][[Viikko::>23]][[Viikko::<39]]"\
"|?Havainto|?SiteID|?Vesistö|?Alue|?Kunta|?Viikko|?Päivämäärä|?Levätilanne|?Vuosi|"\
"sort=Päivämäärä|limit=1000000"\
 --data-urlencode "format=json" > data$1.json
