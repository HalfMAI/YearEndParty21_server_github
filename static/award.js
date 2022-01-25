window.onload = (e) => {
    selection_setting(1);
}
let g_tbHeaderList = ["用户是否可抽中多奖品", "用户池", "用户池列表名字", "奖品名字", "奖品数目", "奖品图片名字"];
let g_tbHeaderStatusList = ["max_award_num", "award_num_left"];
let g_LastPayloadList = null;
let g_active_row = null;
let g_old_selected_row = null;
let g_Server_Last_draw_info = null;

function ResetGloableVar() {
    g_LastPayloadList = null;
    g_active_row = null;
    g_old_selected_row = null;
    g_Server_Last_draw_info = null;
}


function GetActivedRowValues(column_dict, active_row=g_active_row, column_list=g_tbHeaderList) {    
    let result_dict = {};
    Array.from(active_row.cells).forEach((cell, col_id) => {
        let tmpColumnName = column_list[col_id];
        if (Object.keys(column_dict).includes(tmpColumnName)) { // just need the header list
            let tmp_value = "";
            tmp_value = cell.querySelector('input').value;
            result_dict[column_dict[tmpColumnName]] = tmp_value;
        }
    });
    return result_dict;
}

function OnSelectAwardPlayerInfoPressed(){
    let get_award_info = {};
    if (g_active_row != null) {
        let column_dict = {"用户池":"pool_id", "奖品名字":"award_name"};
        get_award_info = GetActivedRowValues(column_dict);
    } else {
        return false;
    }

    let url = new URL(window.location.origin + '/selected_award_player_info');
    url.search = new URLSearchParams(get_award_info);
    fetch(url).then(function (response) {
        return response.json();
    }).then(function (data) {
        update_last_draw_info();
        update_chara_info(data);
        update_log(data);
    }).catch(function (e) {
        console.log("OnAllInfoPressed Exception:" + e);
        alert("OnAllInfoPressed Exception:" + e);
    });
}

function OnSelectPoolInfoPressed(){
    let get_pool = {};
    if (g_active_row != null) {        
        let column_dict = { "用户池": "pool_id" };
        get_pool = GetActivedRowValues(column_dict);
    } else {
        return false;
    }
    let url = new URL(window.location.origin + '/pool_info');
    url.search = new URLSearchParams(get_pool);
    fetch(url).then(function (response) {
        return response.json();
    }).then(function (data) {
        update_last_draw_info();
        update_chara_info(data);
        update_log(data);
    }).catch(function (e) {
        console.log("OnAllInfoPressed Exception:" + e);
        alert("OnAllInfoPressed Exception:" + e);
    });
}

function OnAllInfoPressed(){    
    let url = window.location.origin + '/export_all_award_info'

    fetch(url)
    .then(response => response.blob())
    .then(blob => URL.createObjectURL(blob))
    .then(url => {
        window.open(url, '_blank');
        URL.revokeObjectURL(url);
    }).catch(function (e) {
        console.log("OnAllInfoPressed Exception:" + e);
        alert("OnAllInfoPressed Exception:" + e);
    });;
}

function OnDrawPressed(stage){
    let draw_num = document.querySelector("#submit_draw_num").value;
    if (g_Server_Last_draw_info == null) {
        let draw_award = {};
        if (g_active_row != null) {        
            let column_dict = {"用户池":"draw_pool_id", "奖品名字":"draw_award_name"};
            draw_award = GetActivedRowValues(column_dict);
        } else {
            return false;
        }    
        draw_award["draw_num"] = draw_num;
        start_draw(draw_award, stage);
    } else {
        g_Server_Last_draw_info["draw_num"] = draw_num;     // the new num can be used
        start_draw(g_Server_Last_draw_info, stage);
    }
}

function CheckDrawStageAndUpdateUI(){
    let url = window.location.origin + '/check_draw_stage'
    fetch(url).then(function (response) {
        return response.json();
    }).then(function (data) {
        let cur_draw_stage = data["payload"]["draw_stage"];
        let cur_last_drawed_award_info = data["payload"]["last_draw_award_info"]["drawed_award_info"];
        let cur_last_drawed_player_info = data["payload"]["last_draw_award_info"]["drawed_player_info"];
        console.log("CheckDrawStageAndUpdateUI, Current stage: " + cur_draw_stage);
        SetupDrawStageAndUpdateUI(cur_draw_stage, cur_last_drawed_award_info, cur_last_drawed_player_info);
    }).catch(function (e) {        
        console.log("CheckDrawStage Exception:" + e);
        alert("CheckDrawStage Exception:" + e);
    });
}

function OnStopDrawAnimationPressed(){
    let url = window.location.origin + '/set_stop_animation'
    fetch(url).then(function (response) {
        return response.json();
    }).then(function (data) {
        CheckDrawStageAndUpdateUI();
    }).catch(function (e) {        
        console.log("OnStopDrawAnimationPressed Exception:" + e);
        alert("OnStopDrawAnimationPressed Exception:" + e);
    });
}

function OnCancleDrawStageToInitPressed(){
    if (confirm("请确认，你正在进行【取消抽奖】") == false){
        return;
    }

    let url = window.location.origin + '/cancle_draw_to_init_stage'
    fetch(url).then(function (response) {
        return response.json();
    }).then(function (data) {
        CheckDrawStageAndUpdateUI();
    }).catch(function (e) {        
        console.log("OnCancleDrawStageToInitPressed Exception:" + e);
        alert("OnCancleDrawStageToInitPressed Exception:" + e);
    });
}

function start_draw(post_data, draw_stage) {
    let confirmStr = "";
    let shouldUpdateUI = true;
    switch (draw_stage) {
        case DrawStage.Stage_StartDrawAnimation:
            confirmStr = "请再三确认你需要进行【抽奖，并播放循环动画】";
            post_data['draw_stage'] = DrawStage.Stage_StartDrawAnimation;
            shouldUpdateUI = true;
            break;
        case DrawStage.Stage_BeforeDraw:
            confirmStr = "请再三确认你需要进行【播放准备抽奖界面,此操作后续‘只能继续抽取当前选择奖品’】";
            post_data['draw_stage'] = DrawStage.Stage_BeforeDraw;
            shouldUpdateUI = false;
            break;
    
        default:
            alert("异常阶段："+draw_stage);
            return;
    }
    if (confirm(confirmStr)) {        
        post_data = JSON.stringify(post_data);
        post_data = encodeURI(post_data, "utf-8");
        let url = window.location.origin + '/startdrawing'
        fetch(url, {
            method: 'POST',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json;charset=UTF-8',
            body: post_data
        }).then(function (response) {
            return response.json();
        }).then(function (data) {
            let cur_code = String(data['code']);
            let isShowAlertLog = true;
            if (cur_code == "1000" || cur_code == "2000"){
                isShowAlertLog = false;
            }
            update_log(data, isShowAlertLog);            
            if (shouldUpdateUI) {
                update_chara_info(data);            
            }
            CheckDrawStageAndUpdateUI();
        }).catch(function (e) {
            console.log("test_draw Exception:" + e);
            alert("test_draw Exception:" + e);
        });
    }
}

function edit_awrd() {
    if (confirm("请再三确认你需要更新抽奖信息")) {

        let tmp_award_list = []
        let tb = document.querySelector("#update_table_list");
        Array.from(tb.rows).forEach((tr, row_id) => {
            if (row_id > 0) { //skip the header
                let tmp_curaward = {};
                Array.from(tr.cells).forEach((cell, col_id) => {
                    if (col_id < g_tbHeaderList.length) { // just need the header list
                        let tmp_value = "";
                        tmp_value = cell.querySelector('input').value;
                        
                        tmp_curaward[g_tbHeaderList[col_id]] = tmp_value;
                    }
                });
                tmp_award_list.push(tmp_curaward);
            }
        });

        if (tmp_award_list.length == 0) {
            return;
        }

        let post_data = {
            "save_filename": "awards.csv",
            "award_dict": tmp_award_list
        };
        post_data = JSON.stringify(post_data);
        post_data = encodeURI(post_data, "utf-8");
        let url = window.location.origin + '/update_award_info'
        fetch(url, {
            method: 'POST',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json;charset=UTF-8',
            body: post_data
        }).then(function (response) {
            return response.json();
        }).then(function (data) {
            if (String(data['code']) == '1000') {
                check_awards_status_and_update_table("#update_table_list", true, false);
            }
            update_log(data, true);
        }).catch(function (e) {
            console.log("edit_awrd Exception:" + e);
            alert("edit_awrd Exception:" + e);
        });
    }
}

function check_awards_status_and_update_table(tabId, isCanEdit, isUpdateLog=true, isCanSelect=true) {
    let t_body = document.querySelector(tabId).querySelector('tbody');
    t_body.innerHTML = "";
    let url = window.location.origin + '/cur_award_info'
    fetch(url).then(function (response) {
        return response.json();
    }).then(function (data) {
        if (isUpdateLog) {
            update_log(data);
        }
        update_table(tabId, data, isCanEdit, isCanSelect);
    }).catch(function (e) {
        console.log("checkresult Exception:" + e);
        alert("checkresult Exception:" + e);
    });
}

function init_all_status() {
    if (confirm("请再三确认你需要重置所有状态")) {
        if (confirm("重置所有状态，将会把所有抽奖过记录进行清除！！请确认的确需要清除")) {
            let url = window.location.origin + '/init_all_status'
            fetch(url).then(function (response) {
                return response.json();
            }).then(function (data) {
                update_log(data, true);
            }).catch(function (e) {
                console.log("init_all_status Exception:" + e);
                alert("init_all_status Exception:" + e);
            });
        }
    }
}

function reproccess_all_images() {
    if (confirm("此操作将重新压缩并转格式所有图片,这个操作并不太影响,只会花费一点IO时间")) {
        let url = window.location.origin + '/reproccess_all_images_format'
        fetch(url).then(function (response) {
            return response.json();
        }).then(function (data) {
            update_log(data, true);
        }).catch(function (e) {
            console.log("reproccess_all_images Exception:" + e);
            alert("reproccess_all_images Exception:" + e);
        });
    }
}

function update_table(id, data, isCanEdit, isCanSelect=true) {
    if (g_active_row != null) {g_active_row = null;}
    
    let t_head = document.querySelector(id).querySelector('thead');
    t_head.innerHTML = "";
    let t_body = document.querySelector(id).querySelector('tbody');
    t_body.innerHTML = "";

    let cur_code = String(data['code'])
    if (cur_code == '1000'|| cur_code== '1001') {
        let tr = document.createElement('tr');        
        let tmp_headers_combine = g_tbHeaderList.concat(g_tbHeaderStatusList);
        tmp_headers_combine.forEach((headName) => {     
            let td = document.createElement('td');
            td.innerText = headName;
            tr.appendChild(td);
        });
        t_head.appendChild(tr);

        payload_list = data['payload'];
        payload_list.forEach((award, index) => {
            let tr = create_row(award, isCanEdit, null, isCanSelect);
            t_body.appendChild(tr);
        });
        g_LastPayloadList = payload_list;
    }
}

function add_new_row() {
    let t_body = document.querySelector("#update_table_list").querySelector('tbody');
    if (t_body.rows.length <=0) {
        return;
    }
    let tmpAward = g_LastPayloadList[g_LastPayloadList.length-1];
    tmpAward["award_num_left"] = tmpAward["max_award_num"];     // reset the draw status
    let tr = create_row(tmpAward, true, "lightblue");
    t_body.appendChild(tr);
}

function remove_actived_row() {
    if (g_active_row == null) { return; }
    if(confirm("请确认是否删除选中行?") == false) {        
        return;
    }    
    tmpAward = GetActivedRowValues({"max_award_num":"max_award_num", "award_num_left":"award_num_left"}, g_active_row, g_tbHeaderList.concat(g_tbHeaderStatusList));
    if (parseInt(tmpAward["max_award_num"]) - parseInt(tmpAward["award_num_left"]) != 0){
        alert("请不要删除已经抽取过的奖品,删除了也不会生效");
        return;
    }

    let t_body = document.querySelector("#update_table_list").querySelector('tbody');
    if (g_active_row != null) {
        t_body.removeChild(g_active_row);
        g_active_row = null;
    }
}

function create_row(award=null, isCanEdit=true, sp_background=null, isCanSelect=true) {    
    let tr = document.createElement('tr');
    
    let hold_list = ["用户是否可抽中多奖品", "用户池", "用户池列表名字", "奖品名字"];
    let isAwardAleadyDrawed = false;    
    if (award) {
        if (parseInt(award["max_award_num"]) - parseInt(award["award_num_left"]) != 0){
            isAwardAleadyDrawed = true;
        }        
    }
    g_tbHeaderList.forEach(t_h => {
        let tmp_value = "";
        let tmpCanEdit = isCanEdit;
        if (award) {
            tmp_value = award[t_h];
            if (hold_list.includes(t_h) && isAwardAleadyDrawed == true) {  // just freeze the ids columns
                tmpCanEdit = false;
                sp_background = 'lavender';
                if (parseInt(award["award_num_left"]) == 0) {  // just make a different color
                    sp_background = 'rosybrown';
                }
            }
        }
        let td = createCell(t_h, tmp_value, tmpCanEdit, sp_background, isCanSelect);
        tr.appendChild(td);
    });
    g_tbHeaderStatusList.forEach(t_h => {
        let tmp_value = ""
        if (award) {
            tmp_value = award[t_h];
        }
        let td = createCell(t_h, tmp_value, false, sp_background, isCanSelect);
        tr.appendChild(td);
    });
    return tr
}

function selection_setting(pageIndex) {
    let e_1 = document.querySelector("#div_test_draw");
    let e_2 = document.querySelector("#div_check_award");
    let e_3 = document.querySelector("#div_init_all_status");
    let e_4 = document.querySelector("#div_edit_award");

    let e_list = [e_1, e_2, e_3, e_4];
    e_list.forEach(element => {
        if (element) {
            element.hidden = true;
        }
    });
    e_list[pageIndex].hidden = false;

    if (pageIndex == 1) {
        CheckDrawStageAndUpdateUI();
    } else if (pageIndex == 3) {
        check_awards_status_and_update_table("#update_table_list", true);
    }

    let t_e = document.querySelector("#response_text");
    t_e.innerText = "";
    
    ResetGloableVar();
}

function createCell(columnName, inputValue="", canEdit=false, sp_background=null, canSelect=true) {
    let td = document.createElement("td");
    let tdInput = document.createElement("input");

    tdInput.setAttribute("value", inputValue);

    if (columnName == "用户是否可抽中多奖品"){
        tdInput.type = "checkbox";
        if (inputValue == "是"){
            tdInput.checked = true;
        } else {
            tdInput.checked = false;
        }
        tdInput.oninput = function (){
            if (this.checked){
                this.value = "是";
            } else {
                this.value = "否";
            }
        }
    } else {        
        tdInput.type = "text";
        tdInput.classList.add("form-control");
        tdInput.style.setProperty("font-weight", "bold");
        tdInput.style.setProperty("font-size", "14px");
    }

    if (canEdit == false) {
        tdInput.readOnly = true;
        tdInput.style.setProperty("background", "lightgrey");
        if (tdInput.type == "checkbox") {
            tdInput.disabled = true;
        }
    }
    td.appendChild(tdInput);

    if (canSelect == true) {
        tdInput.onfocus = function(){
            update_G_Active_row(this.parentElement.parentElement);
        }
        tdInput.onchange = function(){
            this.parentElement.style.setProperty("background", "tomato");
        }
        if (columnName == "奖品数目"){
            tdInput.oninput = function(){
                this.value = this.value.replace(/[^0-9]/g, '').replace(/(\..*?)\..*/g, '$1');
            }
        }
    }

    if (sp_background != null){
        tdInput.parentElement.style.setProperty("background", sp_background);
    }

    return td;
}

function update_G_Active_row(row) {
    if (g_active_row != null) {
        g_active_row.classList.remove("cur_select");
    }

    g_active_row = row;
    g_active_row.classList.add("cur_select");

    g_old_selected_row = g_active_row;
}

function update_log(data, isShouldAlert=false) {
    let t_e = document.querySelector("#response_text");
    let result_text = JSON.stringify(data, null, "\t");
    t_e.innerText = result_text
    
    if (isShouldAlert) {
        alert(result_text);
    }
}


function reset_chara_info_table(){
    let t_head = document.querySelector("#check_hold_award_table_list").querySelector('thead');
    t_head.innerHTML = "";
    let t_body = document.querySelector("#check_hold_award_table_list").querySelector('tbody');
    t_body.innerHTML = "";
}


function update_last_draw_info(isJustClear=false){    
    let tLastDrawInfoDiv = document.querySelector("#last_draw_info");
    tLastDrawInfoDiv.innerHTML = "";
    

    let tmpLastDrawAward_info = g_Server_Last_draw_info;
    if (g_old_selected_row != null) {
        const column_dict = {"用户池":"上次选择用户池名字", "奖品名字":"上次选择奖品名字"}
        tmpLastDrawAward_info = GetActivedRowValues(column_dict, g_old_selected_row);
    } else {
        tmpLastDrawAward_info["上次选择用户池名字"] = tmpLastDrawAward_info["draw_pool_id"];
        tmpLastDrawAward_info["上次选择奖品名字"] = tmpLastDrawAward_info["draw_award_name"];
    }
    
    let tmp_headers = ["上次选择用户池名字", "上次选择奖品名字"];
    tmp_headers.forEach((headName) => {
        let tP = document.createElement("p");
        tP.classList.add("fw-bold");
        tP.innerText = headName + ":    " +  "【" + tmpLastDrawAward_info[headName] + "】";
        tLastDrawInfoDiv.appendChild(tP);
    });
}


function update_chara_info(data){    
    let t_head = document.querySelector("#check_hold_award_table_list").querySelector('thead');
    t_head.innerHTML = "";
    let t_body = document.querySelector("#check_hold_award_table_list").querySelector('tbody');
    t_body.innerHTML = "";

    if (data == null) {
        return;
    }
    let cur_code = String(data['code'])
    if (cur_code == '1000') {
        let tr = document.createElement('tr');        
        let charaTableHeaderList = ["player_name", "player_no", 'image_url', "抽中奖品"]
        charaTableHeaderList.forEach((headName) => {     
            let td = document.createElement('td');
            td.innerText = headName;
            tr.appendChild(td);
        });
        t_head.appendChild(tr);

        payload_list = data['payload'];
        payload_list.forEach((award, index) => {
            let tr = document.createElement('tr');
            charaTableHeaderList.forEach(t_h => {
                let tmp_value = ""
                if (award) {
                    tmp_value = award[t_h];
                }
                let td = createCell(t_h, tmp_value, false, null, false);
                tr.appendChild(td);
            });
            t_body.appendChild(tr);
        });
    }
}


const DrawStage = Object.freeze({
    Stage_Init : "Stage_Init",
    Stage_BeforeDraw : "Stage_BeforeDraw",
    Stage_StartDrawAnimation : "Stage_StartDrawAnimation",
    Stage_EndDrawAnimation : "Stage_EndDrawAnimation",
});

function SetupDrawStageAndUpdateUI(draw_stage, cur_last_drawed_award_info=null, cur_last_drawed_player_info=null) {
    if (Object.keys(cur_last_drawed_award_info).length > 0){   //check is empty
        g_Server_Last_draw_info = cur_last_drawed_award_info;
    }
    
    let InputDrawNum = document.querySelector("#div_draw_num");
    let BtnReadyToDraw = document.querySelector("#BtnReadyToDraw");
    let BtnDraw = document.querySelector("#BtnStartDraw");
    let BtnStopDraw = document.querySelector("#BtnStopDrawAnimation");
    let BtnCancleDraw = document.querySelector("#BtnCancleReadyDraw");
    
    let Div_PoolInfo_AwardInfo = document.querySelector("#check_pool_or_award_info_div");
    let Div_AwardEdit = document.querySelector("#DivEditSelection");

    InputDrawNum.hidden = true;
    BtnReadyToDraw.hidden = true;
    BtnDraw.hidden = true;
    BtnStopDraw.hidden = true;
    BtnCancleDraw.hidden = true;

    Div_PoolInfo_AwardInfo.hidden = true;

    switch (draw_stage) {
        case DrawStage.Stage_EndDrawAnimation:
        case DrawStage.Stage_Init:
            g_Server_Last_draw_info = null;
            Div_PoolInfo_AwardInfo.hidden = false;
            InputDrawNum.hidden = false;
            BtnReadyToDraw.hidden = false;
            Div_AwardEdit.hidden = false;
            check_awards_status_and_update_table("#check_award_table_list", false, false, true);
            break;
        case DrawStage.Stage_BeforeDraw:
            BtnDraw.hidden = false;
            InputDrawNum.hidden = false;
            BtnCancleDraw.hidden = false;
            Div_AwardEdit.hidden = true;
            check_awards_status_and_update_table("#check_award_table_list", false, false, false);
            update_last_draw_info();

            update_chara_info(null);    // to clear last info
            break;
        case DrawStage.Stage_StartDrawAnimation:
            check_awards_status_and_update_table("#check_award_table_list", false, false, false);
            update_last_draw_info();
            BtnStopDraw.hidden = false;
            Div_AwardEdit.hidden = true;
            break;
    
        default:
            alert("UNKNOW stage :" + String(draw_stage));
            break;
    }
}
