// Gera o mapa coroplético da eleição presidencial 2026 a partir da API do TSE
// e da malha territorial do IBGE. Uso: node gerar_mapa.mjs
import { readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const AQUI = dirname(fileURLToPath(import.meta.url));
const UFS = ["AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG",
             "PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SE","SP","TO"];
const TURNOS = { "6257": "t1", "6258": "t2" }; // 04/10 e 25/10/2026
const NOMES = {
  AC:"Acre", AL:"Alagoas", AP:"Amapá", AM:"Amazonas", BA:"Bahia", CE:"Ceará",
  DF:"Distrito Federal", ES:"Espírito Santo", GO:"Goiás", MA:"Maranhão",
  MT:"Mato Grosso", MS:"Mato Grosso do Sul", MG:"Minas Gerais", PA:"Pará",
  PB:"Paraíba", PR:"Paraná", PE:"Pernambuco", PI:"Piauí", RJ:"Rio de Janeiro",
  RN:"Rio Grande do Norte", RS:"Rio Grande do Sul", RO:"Rondônia", RR:"Roraima",
  SC:"Santa Catarina", SE:"Sergipe", SP:"São Paulo", TO:"Tocantins"
};
const COD2UF = { 11:"RO",12:"AC",13:"AM",14:"RR",15:"PA",16:"AP",17:"TO",21:"MA",
  22:"PI",23:"CE",24:"RN",25:"PB",26:"PE",27:"AL",28:"SE",29:"BA",31:"MG",
  32:"ES",33:"RJ",35:"SP",41:"PR",42:"SC",43:"RS",50:"MS",51:"MT",52:"GO",53:"DF" };

async function pegarJSON(url) {
  const r = await fetch(url, { headers: { "User-Agent": "mapa-eleicao-2026/1.0" } });
  if (!r.ok) throw new Error(`${r.status} ${url}`);
  return r.json();
}

function candidatos(json) {
  const carg = (json.carg || []).find(c => c.cd === "1");
  if (!carg) throw new Error("cargo Presidente não encontrado");
  const out = [];
  for (const agr of carg.agr || [])
    for (const par of agr.par || [])
      for (const c of par.cand || [])
        out.push({ sg: par.sg, nm: c.nmu || c.nm, v: Number(c.vap), p: Number(String(c.pvap).replace(",", ".")) });
  out.sort((a, b) => b.v - a.v);
  return out;
}

function resumoUF(json) {
  return {
    tv: Number(json.v.tv), vvc: Number(json.v.vvc), vb: Number(json.v.vb), vn: Number(json.v.tvn),
    te: Number(json.e.te), pcomp: Number(String(json.e.pc).replace(",", ".")),
    secoes: `${json.s.st}/${json.s.ts}`,
    dg: json.dg, hg: json.hg, and: json.and,
    cands: candidatos(json)
  };
}

// ---- votos por UF (27 UFs x 2 turnos) ----
const ufs = {};
let feitos = 0;
await Promise.all(UFS.flatMap(uf =>
  Object.entries(TURNOS).map(async ([ele, t]) => {
    const pad = ele.padStart(6, "0");
    const url = `https://resultados.tse.jus.br/oficial/ele2026/${ele}/dados/${uf.toLowerCase()}/${uf.toLowerCase()}-c0001-e${pad}-u.json`;
    ufs[uf] = ufs[uf] || {};
    ufs[uf][t] = resumoUF(await pegarJSON(url));
    feitos++;
  })
));
console.log(`TSE: ${feitos} arquivos por UF baixados.`);

// ---- totais nacionais ----
const nacional = {};
for (const [ele, t] of Object.entries(TURNOS)) {
  const pad = ele.padStart(6, "0");
  const j = await pegarJSON(`https://resultados.tse.jus.br/oficial/ele2026/${ele}/dados/br/br-c0001-e${pad}-u.json`);
  nacional[t] = resumoUF(j);
}
console.log("TSE: totais nacionais (BR) baixados.");

// ---- malha territorial IBGE ----
const bruto = await pegarJSON(
  "https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR?formato=application/vnd.geo+json&intrarregiao=UF"
);
console.log(`IBGE: malha com ${bruto.features.length} feições.`);

// arredonda coordenadas e reduz anéis muito densos
function simplificaranel(ring) {
  const passo = ring.length > 500 ? 2 : 1;
  const out = [];
  for (let i = 0; i < ring.length; i += passo) {
    const p = [Math.round(ring[i][0] * 100) / 100, Math.round(ring[i][1] * 100) / 100];
    const ult = out[out.length - 1];
    if (!ult || ult[0] !== p[0] || ult[1] !== p[1]) out.push(p);
  }
  const primeiro = out[0], ultimo = out[out.length - 1];
  if (primeiro && ultimo && (primeiro[0] !== ultimo[0] || primeiro[1] !== ultimo[1])) out.push(primeiro);
  return out;
}
function simplificar(geom) {
  if (geom.type === "Polygon")
    return { type: "Polygon", coordinates: geom.coordinates.map(simplificaranel) };
  if (geom.type === "MultiPolygon")
    return { type: "MultiPolygon", coordinates: geom.coordinates.map(p => p.map(simplificaranel)) };
  return geom;
}
const geo = {
  type: "FeatureCollection",
  features: bruto.features.map(f => ({
    type: "Feature",
    properties: { sigla: COD2UF[Number(f.properties.codarea)], nome: NOMES[COD2UF[Number(f.properties.codarea)]] },
    geometry: simplificar(f.geometry)
  }))
};
const siglas = geo.features.map(f => f.properties.sigla).sort();
console.log("Malha mapeada:", siglas.join(","));

// ---- monta o HTML final ----
const template = await readFile(join(AQUI, "mapa_template.html"), "utf8");
const dados = {
  meta: { gerado: new Date().toLocaleString("pt-BR") },
  nomes: NOMES,
  nacional,
  ufs
};
const html = template
  .replace("/*__DADOS__*/", JSON.stringify(dados))
  .replace("/*__GEO__*/", JSON.stringify(geo));
const destino = join(AQUI, "mapa_eleicao_presidencial_2026.html");
await writeFile(destino, html, "utf8");
console.log(`OK: ${destino} (${(html.length / 1024).toFixed(0)} KB)`);
