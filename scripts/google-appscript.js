// Constants
const WEBHOOK_URL = 'http://your-domain/webhook/sheets';  // Thay thế bằng URL webhook của bạn
const SHEET_NAME = 'Responses';  // Tên sheet chứa dữ liệu

// Thêm menu vào Google Sheets
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('SPA Bot')
    .addItem('Gửi dữ liệu mới', 'sendNewData')
    .addItem('Gửi tất cả dữ liệu', 'sendAllData')
    .addToUi();
}

// Lấy dữ liệu từ sheet
function getSheetData(onlyNew = true) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  const lastRow = sheet.getLastRow();
  const lastCol = sheet.getLastColumn();
  
  if (lastRow <= 1) return null;  // Chỉ có header
  
  // Lấy tất cả dữ liệu
  const range = sheet.getRange(1, 1, lastRow, lastCol);
  const values = range.getValues();
  const headers = values[0];
  
  // Tìm cột user_message và assistant_message
  const userMsgCol = headers.indexOf('user_message');
  const assistantMsgCol = headers.indexOf('assistant_message');
  const sentCol = headers.indexOf('Sent');
  
  if (userMsgCol === -1 || assistantMsgCol === -1) {
    throw new Error('Không tìm thấy cột user_message hoặc assistant_message');
  }
  
  const data = [];
  // Bắt đầu từ row 1 (sau header)
  for (let i = 1; i < values.length; i++) {
    const row = values[i];
    
    // Nếu chỉ lấy dữ liệu mới và row đã được đánh dấu là đã gửi thì bỏ qua
    if (onlyNew && sentCol !== -1 && row[sentCol] === true) continue;
    
    // Kiểm tra dữ liệu hợp lệ
    if (row[userMsgCol] && row[assistantMsgCol]) {
      data.push({
        user_message: row[userMsgCol].toString().trim(),
        assistant_message: row[assistantMsgCol].toString().trim(),
        row_index: i + 1  // Lưu index để đánh dấu sau
      });
    }
  }
  
  return data;
}

// Đánh dấu các dòng đã gửi
function markAsSent(rowIndexes) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  
  // Tìm cột "Sent" một cách chính xác
  let sentCol = -1;
  for (let i = 0; i < headers.length; i++) {
    if (headers[i] === 'Sent') {
      sentCol = i;
      break;
    }
  }
  
  // Nếu chưa có cột "Sent" thì thêm vào
  if (sentCol === -1) {
    // Thêm cột mới và đặt tên
    const newColIndex = sheet.getLastColumn() + 1;
    sheet.getRange(1, newColIndex).setValue('Sent');
    
    // Đánh dấu các dòng đã gửi
    rowIndexes.forEach(rowIndex => {
      sheet.getRange(rowIndex, newColIndex).setValue(true);
    });
  } else {
    // Đánh dấu các dòng đã gửi trong cột hiện có
    // Cộng thêm 1 vì Google Sheets bắt đầu từ 1, không phải 0
    const colIndex = sentCol + 1;
    rowIndexes.forEach(rowIndex => {
      sheet.getRange(rowIndex, colIndex).setValue(true);
    });
  }
}

// Gửi dữ liệu đến webhook
function sendToWebhook(data) {
  if (!data || data.length === 0) {
    SpreadsheetApp.getUi().alert('Không có dữ liệu mới để gửi!');
    return;
  }
  
  const payload = {
    data: data.map(({user_message, assistant_message}) => ({
      user_message,
      assistant_message
    }))
  };
  
  const options = {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify(payload)
  };
  
  try {
    const response = UrlFetchApp.fetch(WEBHOOK_URL, options);
    const responseCode = response.getResponseCode();
    
    if (responseCode === 200) {
      // Đánh dấu các dòng đã gửi thành công
      markAsSent(data.map(item => item.row_index));
      SpreadsheetApp.getUi().alert(`Đã gửi ${data.length} mẫu dữ liệu thành công!`);
    } else {
      throw new Error(`HTTP error ${responseCode}`);
    }
  } catch (error) {
    SpreadsheetApp.getUi().alert('Lỗi khi gửi dữ liệu: ' + error.toString());
  }
}

// Hàm gửi dữ liệu mới
function sendNewData() {
  const data = getSheetData(true);  // Chỉ lấy dữ liệu mới
  sendToWebhook(data);
}

// Hàm gửi tất cả dữ liệu
function sendAllData() {
  const ui = SpreadsheetApp.getUi();
  const response = ui.alert(
    'Xác nhận gửi tất cả dữ liệu',
    'Bạn có chắc chắn muốn gửi lại TẤT CẢ dữ liệu? Điều này có thể tạo ra các bản ghi trùng lặp.',
    ui.ButtonSet.YES_NO
  );
  
  if (response === ui.Button.YES) {
    const data = getSheetData(false);  // Lấy tất cả dữ liệu
    sendToWebhook(data);
  }
}

// Trigger tự động khi có thay đổi trong sheet
function createOnEditTrigger() {
  const triggers = ScriptApp.getProjectTriggers();
  const sheetId = SpreadsheetApp.getActiveSpreadsheet().getId();
  
  // Kiểm tra xem trigger đã tồn tại chưa
  const triggerExists = triggers.some(trigger => 
    trigger.getEventType() === ScriptApp.EventType.ON_EDIT &&
    trigger.getHandlerFunction() === 'onEdit'
  );
  
  if (!triggerExists) {
    ScriptApp.newTrigger('onEdit')
      .forSpreadsheet(sheetId)
      .onEdit()
      .create();
  }
}

// Xử lý sự kiện khi có thay đổi trong sheet
function onEdit(e) {
  const sheet = e.source.getActiveSheet();
  if (sheet.getName() !== SHEET_NAME) return;
  
  const row = e.range.getRow();
  if (row === 1) return;  // Bỏ qua nếu sửa header
  
  // Tự động gửi dữ liệu mới sau 5 giây
  Utilities.sleep(5000);
  sendNewData();
}