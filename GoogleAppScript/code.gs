// ===========================
// ตั้งค่าพื้นฐาน
// ===========================
const SPREADSHEET_ID = '1qs10Pe8kuysAfTCu-Es_zrRJvujqEZKKRMygSojUKlc';
const LOGIN_SHEET_NAME = 'data';     // ชื่อชีตเก็บบัญชีผู้ใช้
const DEFAULT_TRACKING_SHEET = 'Patient0'; 
// ❌ ลบ TOTAL_PATIENTS ออกแล้ว เพื่อให้ระบบนับเองอัตโนมัติ

// ===========================
// ฟังก์ชันหลัก (Routing)
// ===========================
function doGet(e) {
  let page = e.parameter.page || 'index'; 
  let template;

  if (page === 'dashboard') {
    template = HtmlService.createTemplateFromFile('dashboard');
  } else if (page === 'patientDetail') {
    template = HtmlService.createTemplateFromFile('PT');
    template.patientId = e.parameter.id || 0; 
  } else {
    template = HtmlService.createTemplateFromFile('index');
  }

  return template.evaluate()
    .addMetaTag('viewport', 'width=device-width, initial-scale=1')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

function getWebAppUrl() {
  return ScriptApp.getService().getUrl();
}

// ===========================
// ✅ ฟังก์ชันตรวจสอบการล็อกอิน
// ===========================
function checkLogin(username, password, selectedRole) {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const sheet = ss.getSheetByName(LOGIN_SHEET_NAME);
  if (!sheet) throw new Error(`ไม่พบชีตชื่อ '${LOGIN_SHEET_NAME}'`);

  const data = sheet.getDataRange().getValues();
  if (data.length < 2) return { success: false, message: 'ไม่มีบัญชีผู้ใช้ในระบบ' };

  const headers = data[0].map(h => String(h).trim());
  const usernameCol = headers.indexOf('username');
  const passwordCol = headers.indexOf('password');
  const positionCol = headers.indexOf('ตำแหน่ง');
  const fullNameCol = headers.indexOf('ชื่อผู้ใช้');

  if (usernameCol === -1 || passwordCol === -1 || positionCol === -1)
    throw new Error('ไม่พบคอลัมน์ username, password, ตำแหน่ง ในชีต Login');

  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    const storedUsername = String(row[usernameCol] || '').trim();
    
    if (storedUsername === username) {
      const storedPassword = String(row[passwordCol] || '').trim();
      if (storedPassword != password) {
         return { success: false, field: 'password', message: 'รหัสผ่านไม่ถูกต้อง' };
      }

      const storedFullName = fullNameCol !== -1 ? String(row[fullNameCol] || '').trim() : 'User';
      return { success: true, position: 'dashboard', fullName: storedFullName };
    }
  }

  return { success: false, field: 'username', message: 'ไม่พบชื่อผู้ใช้' };
}

// ===========================
// 🆕 ฟังก์ชันสร้างผู้ป่วยใหม่ (Add New Patient)
// ===========================
function addNewPatient(name, code) {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const sheets = ss.getSheets();
  
  // 1. หาหมายเลข Patient ล่าสุด โดยการสแกนชื่อ Sheet ทั้งหมด
  let maxIndex = -1;
  sheets.forEach(s => {
    const sName = s.getName();
    if (sName.startsWith('Patient')) {
       // ตัดคำว่า Patient ออก แล้วดูว่าเป็นเลขอะไร
       const num = parseInt(sName.replace('Patient', ''));
       if (!isNaN(num) && num > maxIndex) maxIndex = num;
    }
  });

  // 2. กำหนดชื่อ Sheet ใหม่ (เอาเลขล่าสุด + 1)
  const newIndex = maxIndex + 1;
  const newSheetName = 'Patient' + newIndex;

  // 3. สร้างชีตและใส่หัวตาราง
  let newSheet = ss.insertSheet(newSheetName);
  
  // -- ส่วนหัวตารางบันทึกการกินยา (Col A, B) --
  newSheet.getRange("A1").setValue("วันที่");
  newSheet.getRange("B1").setValue("เวลา");

  // -- ส่วนข้อมูลส่วนตัว (Col D - J) แถว 1 และ 2 --
  const headers = [["ชื่อ-สกุล", "รหัส", "อายุ", "เพศ", "ที่อยู่", "เบอร์โทร", "แพทย์ผู้ดูแล"]];
  newSheet.getRange("D1:J1").setValues(headers).setBackground("#d9f2e6").setFontWeight("bold");

  // ใส่ข้อมูลเริ่มต้นที่ได้รับมา
  newSheet.getRange("D2").setValue(name);
  newSheet.getRange("E2").setValue(code);
  newSheet.getRange("F2:J2").setValue("-"); // ใส่ขีดไว้ก่อน

  return { 
    success: true, 
    message: 'เพิ่มผู้ป่วย ' + name + ' เรียบร้อย (' + newSheetName + ')' 
  };
}

// ===========================
// 📊 ฟังก์ชันสำหรับ Dashboard (แบบ Dynamic)
// ===========================
function getDashboardStats() {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  let patientsList = [];
  
  const today = new Date();
  const todayStr = Utilities.formatDate(today, Session.getScriptTimeZone(), "yyyy-MM-dd");
  
  let takenCount = 0;
  let notTakenCount = 0;

  // ✅ เปลี่ยนจาก For Loop เป็น While Loop
  // วนลูปหา Patient0, Patient1... ไปเรื่อยๆ จนกว่าจะหาไม่เจอ
  let i = 0;
  while (true) {
    const sheetName = 'Patient' + i;
    const sheet = ss.getSheetByName(sheetName);
    
    // ⛔️ ถ้าหาชีตชื่อนี้ไม่เจอ แสดงว่าหมดคนไข้แล้ว ให้หยุดวนลูป
    if (!sheet) break; 

    // ดึงข้อมูลส่วนตัว
    const infoRange = sheet.getRange("D2:E2"); 
    const info = infoRange.getValues()[0];
    const name = info[0] || ('ผู้ป่วย ' + i);
    const code = info[1] || ('P-' + i);
    
    // เช็คการกินยา (แถวล่าสุด)
    const lastRow = sheet.getLastRow();
    let status = 'not_taken';
    let progress = 0;

    if (lastRow >= 2) { 
      const lastDateVal = sheet.getRange(lastRow, 1).getValue(); 
      if (lastDateVal instanceof Date) {
        const lastDateStr = Utilities.formatDate(lastDateVal, Session.getScriptTimeZone(), "yyyy-MM-dd");
        if (lastDateStr === todayStr) {
          status = 'taken';
          takenCount++;
        } else {
          notTakenCount++;
        }
      } else {
         notTakenCount++;
      }
      progress = Math.min(100, Math.floor((lastRow - 1) * 2)); 
    } else {
       notTakenCount++;
    }

    patientsList.push({
      id: i, 
      name: name,
      code: code,
      status: status,
      progress: progress
    });

    i++; // ขยับไปคนถัดไป (0 -> 1 -> 2 ...)
  }
  
  return {
    total: patientsList.length,
    taken: takenCount,
    notTaken: notTakenCount,
    patients: patientsList
  };
}

// ===========================
// 🏥 ฟังก์ชันดึงข้อมูลรายบุคคล (แบบ Dynamic Check)
// ===========================
function getPatientData(patientIndex) {
  try {
    const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
    
    // รับค่า Index มา ถ้าไม่มีให้เป็น 0
    let targetIndex = 0;
    if (patientIndex !== undefined && patientIndex !== null) {
       targetIndex = parseInt(patientIndex);
    }

    let targetSheetName = 'Patient' + targetIndex;
    
    const sheet = ss.getSheetByName(targetSheetName);
    // ✅ ถ้าหาชีตไม่เจอ ให้แจ้ง Error ทันที (ไม่ต้องเช็ค TOTAL_PATIENTS แล้ว)
    if (!sheet) throw new Error("❌ ไม่พบข้อมูลของผู้ป่วยรายนี้ (" + targetSheetName + ")");

    const data = sheet.getDataRange().getValues();
    if (data.length < 2) return [];

    // ... (ส่วนค้นหา Header คงเดิม) ...
    let headerRowIndex = -1;
    let headers = [];

    for (let r = 0; r < data.length; r++) {
      const rowLower = data[r].map(v => String(v).trim().toLowerCase());
      if (rowLower.includes('date') || rowLower.includes('day') || rowLower.includes('time') || rowLower.includes('วันที่')) {
        headerRowIndex = r;
        headers = rowLower;
        break;
      }
    }

    if (headerRowIndex === -1) throw new Error("❌ ไม่พบแถวหัวตาราง");

    let dateIndex = headers.indexOf('date');
    if (dateIndex === -1) dateIndex = headers.indexOf('day');
    if (dateIndex === -1) dateIndex = headers.indexOf('วันที่');

    let timeIndex = headers.indexOf('time');
    if (timeIndex === -1) timeIndex = headers.indexOf('เวลา');

    if (dateIndex === -1) throw new Error("❌ ไม่พบคอลัมน์วันที่");

    const result = [];
    for (let i = data.length - 1; i > headerRowIndex; i--) {
      const dateValue = data[i][dateIndex];
      const timeValue = timeIndex !== -1 ? data[i][timeIndex] : '';

      if (!dateValue && !timeValue) continue;

      result.push({
        'วันที่': formatDate(dateValue),
        'เวลา': formatTime(timeValue)
      });
    }

    return result;
  } catch (err) {
    return [{ error: err.message }];
  }
}

// ===========================
// ℹ️ ฟังก์ชันดึงข้อมูลส่วนตัว (แบบ Dynamic Check)
// ===========================
function getPatientInfo(patientIndex) {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  
  let targetIndex = 0;
  if (patientIndex !== undefined && patientIndex !== null) {
     targetIndex = parseInt(patientIndex);
  }

  let targetSheetName = 'Patient' + targetIndex;
  const sheet = ss.getSheetByName(targetSheetName);
  
  if (!sheet) return { name: 'ไม่พบข้อมูล' };
  
  const row = 2; 
  const data = sheet.getRange(row, 4, 1, 7).getValues()[0];

  return {
    name: data[0] || '-',       
    code: data[1] || '-',       
    age: data[2] || '-',        
    gender: data[3] || '-',     
    address: data[4] || '-',    
    phone: data[5] || '-',      
    doctor: data[6] || '-'      
  };
}

// ===========================
// Utility Functions
// ===========================
function formatDate(value) {
  if (!value) return '';
  if (Object.prototype.toString.call(value) === '[object Date]') {
    return Utilities.formatDate(value, Session.getScriptTimeZone(), 'dd/MM/yyyy');
  }
  return value;
}

function formatTime(value) {
  if (!value) return '';
  if (Object.prototype.toString.call(value) === '[object Date]') {
    return Utilities.formatDate(value, Session.getScriptTimeZone(), 'HH:mm');
  }
  return value; 
}
// ===========================
// 🗑️ ฟังก์ชันลบผู้ป่วย (Delete Patient) - เพิ่มใหม่
// ===========================
function deletePatient(patientId) {
  try {
    const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
    const sheetName = 'Patient' + patientId;
    const sheet = ss.getSheetByName(sheetName);
    
    if (!sheet) {
      return { success: false, message: 'ไม่พบแผ่นงาน ' + sheetName };
    }
    
    ss.deleteSheet(sheet); // ลบแผ่นงานทิ้ง
    
    return { success: true, message: 'ลบข้อมูล ' + sheetName + ' เรียบร้อยแล้ว' };
  } catch (e) {
    return { success: false, message: 'เกิดข้อผิดพลาด: ' + e.message };
  }
}

// ===========================
// 📊 ปรับปรุง Dashboard ให้รองรับการลบ (อ่านข้ามเลขที่หายไปได้)
// ===========================
// ===========================
// 📊 ปรับปรุง Dashboard (แก้ไข: ดึงข้อมูลส่วนตัวครบ D2:J2)
// ===========================
// ไปที่ไฟล์ Code.gs แล้วแก้ฟังก์ชันนี้ครับ

function getDashboardStats() {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const allSheets = ss.getSheets(); 
  
  let patientsList = [];
  const today = new Date();
  const todayStr = Utilities.formatDate(today, Session.getScriptTimeZone(), "yyyy-MM-dd");
  
  let takenCount = 0;
  let notTakenCount = 0;

  allSheets.forEach(sheet => {
    const sheetName = sheet.getName();
    
    // เช็คว่าเป็นแผ่นงานผู้ป่วย
    if (sheetName.startsWith('Patient')) {
      const idPart = sheetName.replace('Patient', '');
      const id = parseInt(idPart);
      
      if (!isNaN(id)) { 
        
        // 🔴 จุดสำคัญที่ต้องแก้: เปลี่ยนจาก D2:E2 เป็น D2:J2 เพื่อดึงข้อมูลให้ครบ 🔴
        // D=Name, E=Code, F=Age, G=Gender, H=Address, I=Phone, J=Doctor
        const infoRange = sheet.getRange("D2:J2"); 
        const info = infoRange.getValues()[0];
        
        const name = info[0] || ('ผู้ป่วย ' + id);
        const code = info[1] || ('P-' + id);
        const age = info[2] || '-';      
        const gender = info[3] || '-';   
        // info[4] คือที่อยู่
        const phone = info[5] || '-';    // 👈 บรรทัดนี้คือตัวดึงเบอร์โทร
        const doctor = info[6] || '-';   // 👈 บรรทัดนี้คือตัวดึงชื่อหมอ
        
        // --- ส่วนเช็คการกินยา (เหมือนเดิม) ---
        const lastRow = sheet.getLastRow();
        let status = 'not_taken';
        let progress = 0;

        if (lastRow >= 2) { 
          const lastDateVal = sheet.getRange(lastRow, 1).getValue(); 
          if (lastDateVal instanceof Date) {
            const lastDateStr = Utilities.formatDate(lastDateVal, Session.getScriptTimeZone(), "yyyy-MM-dd");
            if (lastDateStr === todayStr) {
              status = 'taken';
              takenCount++;
            } else {
              notTakenCount++;
            }
          } else {
             notTakenCount++;
          }
          progress = Math.min(100, Math.floor((lastRow - 1) * 2)); 
        } else {
           notTakenCount++;
        }

        // 🔴 ส่งข้อมูลกลับไปหน้าเว็บให้ครบ 🔴
        patientsList.push({
          id: id, 
          name: name,
          code: code,
          age: age,        
          gender: gender,  
          phone: phone,    // 👈 ต้องส่งตัวแปรนี้กลับไป
          doctor: doctor,  
          status: status,
          progress: progress
        });
      }
    }
  });
  
  // เรียงลำดับ
  patientsList.sort((a, b) => a.id - b.id);
  
  return {
    total: patientsList.length,
    taken: takenCount,
    notTaken: notTakenCount,
    patients: patientsList
  };

}
// ===========================
// 🆕 ฟังก์ชันสร้างผู้ป่วยใหม่ (บันทึกข้อมูลครบถ้วน)
// ===========================
function addNewPatient(name, code, age, gender, address, phone, doctor) {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const sheets = ss.getSheets();
  
  // 1. หาหมายเลข Patient ล่าสุด
  let maxIndex = -1;
  sheets.forEach(s => {
    const sName = s.getName();
    if (sName.startsWith('Patient')) {
       const num = parseInt(sName.replace('Patient', ''));
       if (!isNaN(num) && num > maxIndex) maxIndex = num;
    }
  });

  // 2. กำหนดชื่อ Sheet ใหม่
  const newIndex = maxIndex + 1;
  const newSheetName = 'Patient' + newIndex;

  // 3. สร้างชีตและใส่หัวตาราง
  let newSheet = ss.insertSheet(newSheetName);
  
  // -- ส่วนหัวตารางบันทึกการกินยา (Col A, B) --
  newSheet.getRange("A1").setValue("Date");
  newSheet.getRange("B1").setValue("Time");

  // -- ส่วนข้อมูลส่วนตัว (Col D - J) --
  const headers = [["ชื่อ-สกุล", "รหัส", "อายุ", "เพศ", "ที่อยู่", "เบอร์โทร", "แพทย์ผู้ดูแล"]];
  newSheet.getRange("D1:J1").setValues(headers)
    .setBackground("#d9f2e6")
    .setFontWeight("bold")
    .setHorizontalAlignment("center");

  // 4. บันทึกข้อมูลที่ได้รับมาลงแถวที่ 2
  // D=Name, E=Code, F=Age, G=Gender, H=Address, I=Phone, J=Doctor
  const patientData = [[
    name, 
    code, 
    age || '-', 
    gender || '-', 
    address || '-', 
    phone || '-', 
    doctor || '-'
  ]];
  
  newSheet.getRange("D2:J2").setValues(patientData);

  return { 
    success: true, 
    message: 'เพิ่มผู้ป่วย ' + name + ' เรียบร้อย (' + newSheetName + ')' 
  };
}
// ===========================
// ✏️ ฟังก์ชันแก้ไขข้อมูลผู้ป่วย (Update Patient)
// ===========================
function updatePatientInfo(patientId, updatedData) {
  try {
    const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
    const sheetName = 'Patient' + patientId;
    const sheet = ss.getSheetByName(sheetName);
    
    if (!sheet) {
      return { success: false, message: 'ไม่พบแผ่นงาน ' + sheetName };
    }

    // ข้อมูลที่จะบันทึก (เรียงตามลำดับ D, E, F, G, H, I, J)
    // ชื่อ, รหัส, อายุ, เพศ, ที่อยู่, เบอร์โทร, แพทย์
    const rowData = [[
      updatedData.name,
      updatedData.code,
      updatedData.age,
      updatedData.gender,
      updatedData.address,
      updatedData.phone,
      updatedData.doctor
    ]];

    // บันทึกทับลงไปที่แถว 2 คอลัมน์ D ถึง J
    sheet.getRange("D2:J2").setValues(rowData);

    return { success: true, message: 'บันทึกการแก้ไขเรียบร้อยแล้ว' };

  } catch (e) {
    return { success: false, message: 'เกิดข้อผิดพลาด: ' + e.message };
  }
}

