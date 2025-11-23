import requests

def copy_sheet_via_gas(script_url, spreadsheet_id, source_name, name_prefix):
    """
    ส่งคำสั่งไปที่ Google Apps Script เพื่อให้ Copy Sheet แบบรันเลขต่ออัตโนมัติ
    """
    # ข้อมูลที่จะส่งไป
    payload = {
        "spreadsheetId": spreadsheet_id,
        "sourceSheetName": source_name,
        "newSheetName": name_prefix # ส่งไปแค่คำนำหน้า เช่น "Patient"
    }
    
    try:
        # ส่งข้อมูลด้วย POST request
        response = requests.post(script_url, json=payload)
        
        if response.status_code == 200:
            # แสดงผลลัพธ์ที่ส่งกลับมาจาก Google (จะบอกชื่อใหม่ที่ตั้งให้ด้วย)
            print(f"ผลลัพธ์จาก Google: {response.text}")
        else:
            print(f"เกิดข้อผิดพลาดในการเชื่อมต่อ: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")

# --- การใช้งาน ---
if __name__ == "__main__":
    # URL Web App ของคุณ (อย่าลืม Deploy เป็น New Version ก่อนนะครับ)
    GAS_URL = "https://script.google.com/macros/s/AKfycbwls7Fl6tVQnzJdqx94J-dkAigtE6H0QsFZD5gs4-YgWmKni-H2f62nsY5xw1q0gGV_0g/exec" 
    
    SHEET_ID = "1ZndbpuQx0-PBIlXOdcfD9eKPfQMI5TOWhzM8lOLdEo8"
    
    # ต้นฉบับชื่อ "Patient0"
    # ต้องการสร้างใหม่โดยใช้คำนำหน้าว่า "Patient" 
    # (ระบบจะเช็คเอง ถ้ามี Patient5 จะสร้าง Patient6 ให้)
    copy_sheet_via_gas(GAS_URL, SHEET_ID, "Patient0", "Patient")