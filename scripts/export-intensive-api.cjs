// Export the exact course bank used by the UI; no separate hand-maintained keys.
const fs=require('node:fs');
const read=n=>JSON.parse(fs.readFileSync(`src/data/${n}.json`,'utf8'));
const exercises=read('intensive-topic-exercises');
for(const name of ['intensive-exercises-foundation','intensive-exercises-advanced']){
 if(!fs.existsSync(`src/data/${name}.json`))throw Error(`${name} is required`);
 for(const [id,qs] of Object.entries(read(name)))exercises[id]=[...(exercises[id]||[]),...qs];
}
fs.writeFileSync('api/intensive_course_data.json',JSON.stringify({modules:read('intensive-grammar-map'),words:read('intensive-vocabulary'),skills:read('intensive-skills'),exercises}));
