# Kịch bản test — `search_products` và `get_fashion_knowledge`

Kịch bản test thủ công (manual QA) cho 2 tool trong `src/ai_stylist/services/agent/tools.py`,
dựa trên dữ liệu thật đang seed:

- Product DB: `scripts/seeds/products.json` — 50 sản phẩm thật (`SM-PRD-001`..`050`), 3 slot
  (`top`: 26, `bottom`: 22, `dress`: 2), giá 199.000–1.299.000 VND, demographic
  `MALE`/`FEMALE`/`UNISEX`. **Không có sản phẩm nào thuộc `shoes`/`bag`/`accessory`.**
- Knowledge Graph: `scripts/seeds/knowledge_graph.json` — 36 concepts, 74 edges, 39 rules,
  ngưỡng resolve `concept_similarity_threshold = 0.65` (cosine similarity qua Qdrant).

Cách chạy thủ công: gọi trực tiếp tool qua Python REPL hoặc qua chat thật (`/v1/sessions/{id}/messages`)
với câu hỏi tương ứng, rồi đối chiếu kết quả với "Kỳ vọng".

---

## A. `search_products`

Tham số: `query` (bắt buộc), `target` (top/bottom/dress/shoes/bag/accessory, optional),
`limit` (mặc định 8), `price_min`, `price_max`.

| ID | Input | Kỳ vọng | Vì sao |
|----|-------|---------|--------|
| SP01 | `query="áo thun nam"`, `target="top"` | Trả về sản phẩm có category `Áo thun`, `target_demographic` là `MALE` hoặc `UNISEX` (không có `FEMALE`-only) | Catalog có 7 sản phẩm `Áo thun` (219k–329k), đủ 3 demographic; test lọc đúng giới tính từ text query |
| SP02 | `query="đầm dự tiệc"`, `target="dress"` | Trả về đúng 2 sản phẩm: "Đầm Midi Cổ Vuông" (899k), "Đầm Sơ Mi Thắt Eo" (999k) — không nhiều hơn | `dress` slot chỉ có 2 sản phẩm trong toàn catalog, test không bị "ảo giác" thêm sản phẩm không tồn tại |
| SP03 | `query="giày sneaker trắng"`, `target="shoes"` | Trả về **rỗng** (`products: []`) | Catalog không có category giày/shoes nào — đây là khoảng trống dữ liệu thật, không phải bug. Nếu tool trả về sản phẩm không phải giày ở đây thì mới là lỗi |
| SP04 | `query="túi xách"`, `target="bag"` | Trả về **rỗng** | Tương tự SP03 — catalog không có `bag`/`accessory` |
| SP05 | `query="áo sơ mi"`, `price_max=550000` | Chỉ trả sản phẩm ≤ 550k trong nhóm Áo sơ mi (499k, 559k×2, 649k) → phải loại 2 sản phẩm 559k và 649k, chỉ giữ lại sản phẩm 499k | Test đúng biên `price_max` filter, có ít nhất 1 sản phẩm bị loại để phân biệt lọc thật với không lọc |
| SP06 | `query="quần jeans"`, `price_min=850000` | Chỉ giữ 3/5 sản phẩm Quần jeans (859k×2, 929k), loại 2 sản phẩm 799k | Test `price_min`, catalog có đủ range để phân biệt |
| SP07 | `query="áo phông basic"` (không dùng từ "thun") | Vẫn trả về được sản phẩm nhóm `Áo thun` nhờ Qdrant vector search, dù nhánh text-search LIKE của product-service không match chữ "phông" | Test nhánh hybrid: vector search bù được cho từ đồng nghĩa mà LIKE-search literal bỏ lỡ (xem `hybrid_retriever.py`) |
| SP08 | `query="áo tank top nữ tập gym"`, `limit=1` | Trả về đúng 1 sản phẩm | Test `limit` được tôn trọng, không trả dư |
| SP09 | `query="hoodie nam"`, `target="top"` | Trả về trong 2 sản phẩm `Áo hoodie` (799k, 849k), demographic `MALE`/`UNISEX`, không lẫn `FEMALE`-only | Test lọc demographic gián tiếp qua từ khóa "nam" trong query text (tool không có tham số gender riêng) |
| SP10 | `query="áo sơ mi"`, `price_min=2000000` | Trả về **rỗng** dù "áo sơ mi" có match text/vector — vì không sản phẩm nào ≥ 2 triệu | Test price filter override kết quả retrieval khi không có gì thỏa điều kiện giá |
| SP11 | `query="quần jean"` (thiếu "s") | Vẫn trả về sản phẩm nhóm `Quần jeans` | Test độ bền với chính tả/viết tắt lệch nhẹ qua vector search |

---

## B. `get_fashion_knowledge`

Tham số: `terms: list[str]`.

| ID | Input | Kỳ vọng | Vì sao |
|----|-------|---------|--------|
| GK01 | `terms=["đi làm công sở"]` | `resolved_concepts` chứa `OCCASION_OFFICE`; `occasion_rules` có câu "Office outfits should look polished... avoid hoodies, tank tops, and shorts"; `preferred_targets` gồm top (main) + bottom (support) | Test resolve occasion cơ bản, rule đã biết sẵn trong seed |
| GK02 | `terms=["người thấp", "đi biển"]` | 2 concept resolve riêng biệt: `BODY_PETITE` (body_rules: "prefer cleaner vertical lines...") và `OCCASION_BEACH_TRAVEL` (occasion_rules: "breathable fabric and relaxed silhouettes...") | Test resolve nhiều terms cùng lúc, mỗi term map đúng type khác nhau (body_context vs occasion) |
| GK03 | `terms=["dáng người đậm"]` | Resolve `BODY_STOCKY`, `body_rules` chứa "prefer regular fit, clean vertical lines, and avoid overly tight or oversized proportions" | Test riêng cho case đã gây lỗi trước đây (LLM gọi sai chữ "curvy" cho nam thân hình đậm — xem `TC12`/`embedding_service._body_build_query`) |
| GK04 | `terms=["mặc kín đáo, không hở"]` | Resolve `PREF_MODEST`, có key `avoided_items`/modesty rule text "Avoid very short or revealing pieces (shorts, tank tops)..." | Test resolve preference, không phải occasion/item |
| GK05 | `terms=["đám cưới"]` | `resolved_concepts` **rỗng**, trả về `{"message": "Không tìm thấy khái niệm phù hợp", "terms": ["đám cưới"]}` | **Known gap**: KG hiện chưa model occasion "đám cưới/wedding" (chỉ có office/sport/homewear/daily/party/beach). Đây chính là case đã quan sát thấy LLM tự hỏi lại người dùng thay vì trả lời chắc — xác nhận nguyên nhân gốc |
| GK06 | `terms=["việc làm văn phòng", "công sở"]` (2 cách nói khác nhau, cùng nghĩa) | Cả 2 term đều resolve về cùng `concept_id=OCCASION_OFFICE`, nhưng output `resolved_concepts` chỉ có **1 entry** (không lặp) | Test de-dup theo `concept_id` trong `EmbeddingService._resolve_term_specs` (biến `seen_ids`) |
| GK07 | `terms=["office work"]` (tiếng Anh) | Vẫn resolve được `OCCASION_OFFICE` dù model chạy bằng tiếng Việt là chính | Test embedding đa ngôn ngữ của Gemini, không phụ thuộc exact-keyword tiếng Việt |
| GK08 | `terms=["phong cách Hàn Quốc"]` | `resolved_concepts` chứa `STYLE_KOREAN_CASUAL`, nhưng `style_rules`/các list khác đều **rỗng** cho concept này | Concept `STYLE_KOREAN_CASUAL` tồn tại trong KG nhưng chưa gắn rule nào — test tool không "bịa" rule khi không có, chỉ trả resolved_concepts |
| GK09 | `terms=["màu trung tính"]` | Resolve `COLOR_NEUTRAL`, tương tự GK08: concept có nhưng không có rule gắn kèm | Cùng loại gap như GK08 — 2 concept `color` trong seed hiện chưa có rule |
| GK10 | `terms=["xyz random gibberish 12345"]` | `resolved_concepts` rỗng, message "Không tìm thấy khái niệm phù hợp" | Test term hoàn toàn không liên quan thời trang, dưới ngưỡng 0.65 |

---

## Ghi chú khi chạy thật

- SP03/SP04 và GK05/GK08/GK09 là **kỳ vọng rỗng có chủ đích** — nếu tool trả về kết quả khác rỗng
  ở các case này thì cần kiểm tra lại (có thể catalog/KG đã được cập nhật thêm dữ liệu mới).
- Cần Neo4j (`stylemind-neo4j`), Qdrant (`stylemind-qdrant`), và product-service (Java, port 8083)
  đang chạy trước khi test — xem `README.md` phần "Start Infrastructure".
- Nếu muốn tự động hoá các case này thành pytest, có thể theo mẫu
  `tests/test_recommendation_pipeline.py::test_retrieval_case` (đã có `RETRIEVAL_TEST_CASES` cho
  `search_products`/`hybrid_retriever`), nhưng hiện chưa có bộ test tương tự cho `get_fashion_knowledge`.
