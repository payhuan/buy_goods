from pathlib import Path
import json
from PIL import Image, ImageDraw

root=Path(__file__).resolve().parents[1]
catalog=json.loads((root/'assets/catalog.json').read_text(encoding='utf-8'))
for view in ('main','top','front','side'):
    sheet=Image.new('RGB',(1200,900),'#f7f5eb')
    draw=ImageDraw.Draw(sheet)
    for i,item in enumerate(catalog):
        path=root/'assets'/('images/'+item['id']+'.png' if view=='main' else 'diagnostics/'+item['id']+'-'+view+'.png')
        with Image.open(path) as image:
            image=image.resize((300,225))
            sheet.paste(image,((i%4)*300,(i//4)*300),image)
        draw.text(((i%4)*300+12,(i//4)*300+235),item['id'],fill='#243d36')
    sheet.save(root/'verification'/f'contact-{view}.png')
