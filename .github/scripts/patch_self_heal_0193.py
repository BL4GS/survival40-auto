from pathlib import Path
p=Path('survival40-auto/survival40-auto.php')
s=p.read_text(encoding='utf-8')
s=s.replace(' * Version: 0.19.2\\n',' * Version: 0.19.3\\n',1)
s=s.replace("    const VERSION = '0.19.2';","    const VERSION = '0.19.3';",1)
s=s.replace('<h1>Survival40 Auto v0.19.2</h1>','<h1>Survival40 Auto v0.19.3</h1>',1)
p.write_text(s,encoding='utf-8')
