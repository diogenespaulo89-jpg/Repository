# Arquivos de impressão: catálogo inicial de maquetes

São 4 projetos **fictícios**, criados para o catálogo e para gerar conteúdo. Todas as medidas estão em milímetros, e todas as malhas foram verificadas como fechadas (watertight).

| Pasta | Produto | Escala | Tamanho montado |
|---|---|---|---|
| `3mf/1_casa_ipe_1-100` | Casa Ipê, sobrado contemporâneo | 1:100 | 200 x 160 x 70 mm |
| `3mf/2_condominio_recanto_1-500` | Condomínio Recanto das Palmeiras (84 lotes) | 1:500 | 400 x 400 mm |
| `3mf/3_torre_aurora_1-200` | Residencial Aurora (térreo, 14 pavimentos e cobertura) | 1:200 | 160 x 130 x 256 mm |
| `3mf/4_miniatura_aurora` | Miniatura de presente do Aurora | ~1:600 | 76 x 52 x 96 mm |

Cada pasta tem um arquivo **`00_MONTADO_visualizacao.3mf`**, com a maquete montada, para análise. **Não imprima esse arquivo.** Imprima as peças separadas, que já estão na posição certa sobre a mesa.

As imagens de pré-visualização estão em `previews/`.

## Peças e configuração sugerida

As configurações valem para PLA fosco, bico de 0,4 mm e camada de 0,16 a 0,20 mm. **Nenhuma peça precisa de suporte.**

### 1. Casa Ipê (1:100)
| Arquivo | Qtd | Tamanho (mm) | Observações |
|---|---|---|---|
| `A_terreno_e_terreo` | 1 | 200 x 160 x 36 | Terreno, piscina, árvores, térreo com paredes internas e 4 pinos de encaixe |
| `B_laje_e_pavimento_superior` | 1 | 160 x 110 x 32 | Imprimir com a laje sobre a mesa. Encaixa nos pinos do térreo e se retira para mostrar a planta |
| `C_cobertura` | 1 | 134 x 99 x 6 | Cobertura com platibanda, removível |

- Precisa de mesa com pelo menos **210 x 170 mm**.
- **Acabamento:** pintar a piscina de azul ou preencher com resina transparente tingida. Para dar realismo ao vidro, colar acetato nas janelas pelo lado de dentro.

### 2. Condomínio Recanto das Palmeiras (1:500)
| Arquivo | Qtd | Tamanho (mm) | Observações |
|---|---|---|---|
| `base_1_frente_esquerda` a `base_4_fundo_direita` | 1 de cada | 200 x 200 | A base de 400 x 400 mm é dividida em 4. As emendas caem no meio das ruas |
| `placa_20_casas` | 2 | 121 x 111 | 10 casas de cada modelo por placa, totalizando 40 casas |
| `casa_modelo_A` / `casa_modelo_B` | avulsas | 16 x 20 | Para reposição ou para imprimir em outra cor |

- **Montagem:** colar as 4 bases sobre um MDF de 3 mm (de 420 x 420 mm, com borda).
- **Casas removíveis:** cada lote tem um encaixe rebaixado. Na demonstração, a casa retirada indica um lote vendido.
- **Pintura:** ruas em cinza, lotes e lazer em verde (grama de maquete ou tinta) e casas brancas.
- Precisa de mesa com pelo menos **210 x 210 mm**.

### 3. Residencial Aurora (1:200), com iluminação LED
| Arquivo | Qtd | Tamanho (mm) | Observações |
|---|---|---|---|
| `A_terreo_com_jardim` | 1 | 160 x 130 x 29 | Base com nome em relevo, hall envidraçado, marquise e passagem para o cabo do LED |
| `B_pavimento_tipo_imprimir_14x` | **14** | 110 x 88 x 17 | Andar oco, com sacada e guarda-corpo. Pinos em cima e furos embaixo para empilhar |
| `C_cobertura` | 1 | 110 x 80 x 20 | Platibanda, casa de máquinas, caixa d'água e pérgola |

- Cabem de 2 a 4 pavimentos por mesa, conforme o tamanho da mesa.
- **LED:** passar uma fita LED branca quente de 5V pelo centro da torre, com o cabo saindo pelo canal sob a base. Imprimir os pavimentos em PLA branco translúcido deixa a luz mais difusa.
- Se o pino ficar justo, passar uma broca de 2,6 mm nos furos.

### 4. Miniatura de presente
| Arquivo | Uso |
|---|---|
| `miniatura_completa_1_cor.3mf` | Impressão em uma cor |
| `miniatura_2_cores_corpo_e_texto.3mf` | Duas peças (corpo e texto). No fatiador, juntar como um objeto com várias partes e escolher outra cor para o texto (AMS ou MMU) |

- **Para personalizar o texto de cada comprador**, gerar de novo com:
  `python gerar_modelos.py --unidade "APTO 1204 · 2026" --sem-preview`
- Para pedidos em lote, colocar de 6 a 9 miniaturas por mesa.

## Material estimado
O volume sólido de cada peça está em `3mf/resumo_pecas.json`. Com preenchimento de 15% e 3 paredes, a ordem de grandeza é:

| Produto | Volume sólido | Filamento estimado |
|---|---|---|
| Casa Ipê | 259 cm³ | ~180–250 g |
| Condomínio (base e 40 casas) | ~765 cm³ | ~450–600 g |
| Torre Aurora (térreo, 14 andares e cobertura) | ~308 cm³ | ~250–330 g |
| Miniatura (cada) | 106 cm³ | ~40–55 g |

O tempo de impressão e o peso exatos variam com a impressora. Confiram no fatiador (Bambu Studio, OrcaSlicer ou PrusaSlicer).

## Gerar os arquivos de novo
```bash
pip install trimesh manifold3d shapely mapbox_earcut matplotlib lxml networkx
python gerar_modelos.py
```
As medidas ficam no topo de cada função em `gerar_modelos.py`, por exemplo o número de andares, a escala e o tamanho dos lotes.
