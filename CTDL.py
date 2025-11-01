import csv
import json

# ---------------------- Node class ----------------------
class Node:
    def __init__(self, student_id, year_of_study, gpa):
        self.student_id = student_id
        self.year_of_study = year_of_study
        self.gpa = float(gpa)
        self.next = None

    def __repr__(self):
        return f"Node({self.student_id}, {self.year_of_study}, {self.gpa})"

# ---------------------- Khởi tạo mapping head->None ----------------------
def init_heads(head_keys):
    return {h: None for h in head_keys}

# ---------------------- add_tail-----------------------
def add_tail(mapping, head_key, node_to_add):
    if mapping[head_key] is None:
        mapping[head_key] = node_to_add
    else:
        cur = mapping[head_key]
        while cur.next:
            cur = cur.next
        cur.next = node_to_add


# ---------------------- Tìm GPA gần nhất trong khoảng / file ----------------------

def find_nearest_head(head_value, gpas_in_file, sorted_gpas):
    lower = head_value
    upper = head_value + 0.99

    # Candidate trong khoảng
    candidates = [g for g in gpas_in_file if lower <= g <= upper]
    if candidates:
        return min(candidates)

    # Fallback: tìm gpa > upper (giá trị lớn hơn gần nhất)
    for gpa in sorted_gpas:
        if gpa > upper:
            return gpa

    return None


# ---------------------- Đọc CSV, xác định head thực và build khoảng ----------------------
def build_graph_from_csv(csv_file, max_rows=None):
    # base heads cố định
    base_heads = [0.0, 1.0, 2.0, 3.0, 4.0]

    # đọc file CSV vào danh sách student
    students = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            # if max_rows is not None and i >= max_rows:
            #     break
            students.append({
                "id": row['Student ID'],
                "year": int(row['Year of Study']),
                "gpa": float(row['GPA'])
            })

    # lấy danh sách GPA và sorted
    gpas = [s['gpa'] for s in students]
    sorted_gpas = sorted(gpas)

    # Đổi giá trị gần nhất khi head không phải số tròn
    heads_resolved = []
    for hd in base_heads:
        nearest = find_nearest_head(hd, gpas, sorted_gpas)
        # Với 4.0: nếu nearest là None thì ta vẫn muốn giữ 4.0 như key xuất file nhưng không gán node (vì không có số nào lớn hơn)
        if hd == 4.0 and nearest is None:
            heads_resolved.append(4.0)  # giữ 4.0 như key (sẽ có mapping[4.0]=None)
        else:
            if nearest is None:
                # nếu không tìm được và không phải 4.0 -> skip
                continue
            heads_resolved.append(nearest)

    # loại bỏ duplicate (vì nearest có thể tạo các giá trị giống nhau);
    unique_heads = []
    for h in heads_resolved:
        if h not in unique_heads:
            unique_heads.append(h)
    heads_resolved = sorted(unique_heads)

    # init mapping và head_primary
    mapping = init_heads(heads_resolved)
    head_primary = {h: None for h in heads_resolved}

    # Duyệt students theo thứ tự file và add vào mapping
    for stu in students:
        stu_gpa = stu["gpa"]
        # tìm head bucket mà student thuộc về: head <= gpa <= head+0.99
        assigned = False
        for h in heads_resolved:
            if h <= stu_gpa <= h + 0.99:
                node = Node(stu["id"], stu["year"], stu_gpa)
                # nếu head_primary chưa có node và node chính là candidate head (gpa == h), gán
                if head_primary[h] is None and abs(node.gpa - h) < 1e-9:
                    head_primary[h] = node
                add_tail(mapping, h, node)
                assigned = True
                break

    # 7) Sau khi thêm tất cả node, nếu head_primary vẫn None nhưng mapping có node,
    #    chọn node đầu tiên trong mapping[head] làm head_primary
    for h in heads_resolved:
        if head_primary.get(h) is None and mapping.get(h) is not None:
            head_primary[h] = mapping[h]  # node đầu tiên trong linked list

    # Kết thúc: trả về mapping, heads_resolved (sorted), head_primary
    return mapping, heads_resolved, head_primary

# ---------------------- Xuất ra JSON ----------------------
def export_to_json(mapping, heads, head_primary, json_path):

    json_dict = {}

    sorted_heads = sorted(heads)  # đảm bảo thứ tự tăng dần

    for i, head in enumerate(sorted_heads):
        parts = []

        # HEAD: in thông tin full nếu head_primary có node, ngược lại in noval_HEAD
        primary = head_primary.get(head)
        if primary:
            parts.append(f"({primary.gpa}, {primary.student_id}, {primary.year_of_study})")
        else:
            # nếu head là 4.0 và không có node
            parts.append(f"({head}, noval_HEAD, noval_HEAD)")

        # Các node trong khoảng (theo linked list mapping[head])
        cur = mapping.get(head)

        first_node = mapping.get(head)
        cur = first_node
        skip_first = False
        if primary and first_node and abs(primary.gpa - first_node.gpa) < 1e-9 and primary.student_id == first_node.student_id:
            # nếu primary là chính node đầu trong linked list -> khi in nodes ta sẽ bắt đầu từ first_node.next
            skip_first = True
            cur = first_node.next

        # In các node còn lại
        while cur:
            diff = round(cur.gpa - head, 2)
            parts.append(f"({cur.gpa}, {cur.student_id}, {cur.year_of_study})|{diff}")
            cur = cur.next

        # In thông tin nextHead
        if i < len(sorted_heads) - 1:
            next_h = sorted_heads[i + 1]
            next_primary = head_primary.get(next_h)
            if next_primary:
                weight_to_next = round(next_primary.gpa - head, 2)
                parts.append(f"({next_primary.gpa}, {next_primary.student_id}, {next_primary.year_of_study})|{weight_to_next}")
            else:
                # Khi không có GPA 4.0 thì in ra dòng này ở nextHEAD của 3.0
                parts.append(f"({next_h}, noval_nHEAD, noval_nHEAD)|nowei_nHead")
        else:
            # head cuối cùng (không có next) -> pass
            pass

        # Tên head
        json_dict[f"\n\n\n{head}"] = " -> ".join(parts)

    # In 4.0 là noval nếu không có sinh viên có giá trị này
    if 4.0 not in sorted_heads:
        json_dict[f"\n\n\n4.0"] = f"(4.0, noval_HEAD, noval_HEAD)"

    # Ghi file JSON
    with open(json_path, 'w', encoding='utf-8') as jf:
        json.dump(json_dict, jf, indent=4, ensure_ascii=False)


# ---------------------- main ----------------------
if __name__ == "__main__":
    csv_path = "Cleaned_Australian_Student_PerformanceData (ASPD24).csv"
    json_out = "Output.json"
    mapping, heads, head_primary = build_graph_from_csv(csv_path) #Gõ Node để chạy hết file
    export_to_json(mapping, heads, head_primary, json_out)
    print("Đã ghi file JSON thành công:", json_out)