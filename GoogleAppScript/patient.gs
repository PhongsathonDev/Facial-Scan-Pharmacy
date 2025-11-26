// ถ้าในชีตมีคอลัมน์ชื่อ "Timestamp" จะให้ใส่เวลาให้อัตโนมัติ (วัน+เวลา)
const TIMESTAMP_HEADER = "Timestamp";

// เพิ่มหัวคอลัมน์สำหรับวันและเวลาแยกกัน
const DATE_HEADER = "Date";   // ชื่อหัวคอลัมน์สำหรับ "วัน"
const TIME_HEADER = "Time";   // ชื่อหัวคอลัมน์สำหรับ "เวลา"

// ฟังก์ชันหา "แถวว่างตัวแรก" จากด้านบน โดยดูจากคอลัมน์หลัก (เช่น Date หรือ Timestamp)
function getFirstEmptyRow(sheet, baseColIndex1Based) {
  var headerRow = 1;
  var lastRow = sheet.getLastRow();

  // ถ้ายังมีแค่แถวหัวตาราง ก็เริ่มที่แถว 2 เลย
  if (lastRow <= headerRow) {
    return headerRow + 1;
  }

  var startRow = headerRow + 1;
  var numRows = lastRow - headerRow;

  var range = sheet.getRange(startRow, baseColIndex1Based, numRows, 1);
  var values = range.getValues(); // [ [value], [value], ... ]

  for (var i = 0; i < values.length; i++) {
    if (!values[i][0]) {
      // ถ้าเจอเซลล์ว่าง แถวนี้คือแถวแรกที่ว่าง
      return startRow + i;
    }
  }

  // ถ้าไม่มีแถวว่างตรงกลาง ให้เขียนต่อท้าย
  return lastRow + 1;
}

function doPost(e) {
  try {
    if (!e.postData || !e.postData.contents) {
      throw new Error("No POST data");
    }

    // อ่าน JSON ที่ส่งมาจาก Python
    var payload = JSON.parse(e.postData.contents);
    var sheetName = payload.sheet || "Sheet1";
    var rowDataObj = payload.data;

    if (!rowDataObj) {
      throw new Error("No 'data' field in JSON payload");
    }

    var ss = SpreadsheetApp.getActiveSpreadsheet();
    if (!ss) {
      throw new Error("No active spreadsheet.");
    }

    var sheet = ss.getSheetByName(sheetName);
    if (!sheet) {
      throw new Error("Sheet not found: " + sheetName);
    }

    // 1. อ่านหัวตาราง (Headers)
    var headerRow = 1;
    var lastCol = sheet.getLastColumn();
    if (lastCol === 0) {
      throw new Error("No header row found");
    }

    var headerValues = sheet.getRange(headerRow, 1, 1, lastCol).getValues()[0];
    
    // สร้าง Map ชื่อหัวตาราง -> Index (0-based)
    var headerIndexMap = {};
    for (var i = 0; i < headerValues.length; i++) {
      var h = headerValues[i];
      if (h) {
        headerIndexMap[String(h).trim()] = i;
      }
    }

    // 2. หาแถวที่จะเขียนข้อมูล (แถวว่างตัวแรก โดยเช็คจากคอลัมน์ Date หรือ Timestamp)
    var baseColIndex1Based = 1; 
    if (headerIndexMap.hasOwnProperty(DATE_HEADER)) {
      baseColIndex1Based = headerIndexMap[DATE_HEADER] + 1;
    } else if (headerIndexMap.hasOwnProperty(TIMESTAMP_HEADER)) {
      baseColIndex1Based = headerIndexMap[TIMESTAMP_HEADER] + 1;
    }

    var nextRow = getFirstEmptyRow(sheet, baseColIndex1Based);

    // =======================================================
    // 🔴 จุดที่แก้ไข: อ่านข้อมูลเดิมของแถวนั้นขึ้นมาก่อน (Preserve Data)
    // =======================================================
    // ดึงข้อมูลทั้งแถวของ nextRow มาไว้ในตัวแปร currentRowValues
    // ถ้าแถวนั้นมีข้อมูลผู้ป่วยรออยู่ทางขวา มันจะติดมาด้วย ไม่หายไปไหน
    var range = sheet.getRange(nextRow, 1, 1, lastCol);
    var currentRowValues = range.getValues()[0];

    // 3. อัปเดตข้อมูลใหม่ลงไปใน currentRowValues (ทับเฉพาะช่องที่ส่งมา)
    for (var key in rowDataObj) {
      if (!rowDataObj.hasOwnProperty(key)) continue;
      var headerName = String(key).trim();
      
      if (headerIndexMap.hasOwnProperty(headerName)) {
        var colIndex = headerIndexMap[headerName];
        currentRowValues[colIndex] = rowDataObj[key]; // ใส่ค่าใหม่ลงไป
      }
    }

    // ---- จัดการใส่วัน/เวลาอัตโนมัติ ----
    var now = new Date();

    if (headerIndexMap.hasOwnProperty(TIMESTAMP_HEADER)) {
      currentRowValues[headerIndexMap[TIMESTAMP_HEADER]] = now;
    }

    if (headerIndexMap.hasOwnProperty(DATE_HEADER)) {
      var onlyDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      currentRowValues[headerIndexMap[DATE_HEADER]] = onlyDate;
    }

    if (headerIndexMap.hasOwnProperty(TIME_HEADER)) {
      var timeStr = Utilities.formatDate(now, Session.getScriptTimeZone(), "HH:mm:ss");
      currentRowValues[headerIndexMap[TIME_HEADER]] = "'" + timeStr; // ใส่ ' เพื่อให้เป็น Text
    }

    // 4. บันทึกข้อมูลกลับลงไป (Write Back)
    // เขียน currentRowValues กลับลงไปที่เดิม (ข้อมูลทางขวาที่ไม่ได้แก้ก็จะถูกเขียนกลับลงไปเหมือนเดิม)
    range.setValues([currentRowValues]);

    var result = {
      status: "ok",
      sheet: sheetName,
      row: nextRow
    };
    return ContentService
      .createTextOutput(JSON.stringify(result))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    var errorResult = {
      status: "error",
      message: err.message,
      stack: err.stack
    };
    return ContentService
      .createTextOutput(JSON.stringify(errorResult))
      .setMimeType(ContentService.MimeType.JSON);
  }

}