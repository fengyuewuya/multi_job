(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["chunk-16c4d1be"],{"450a":function(t,e,n){"use strict";n.d(e,"c",(function(){return l})),n.d(e,"a",(function(){return o})),n.d(e,"b",(function(){return r})),n.d(e,"d",(function(){return i}));var a=n("b775");function l(){return Object(a["a"])({url:"get_job_summary",method:"get"})}function o(t){return console.log(t),Object(a["a"])({url:"get_job_details?job_id="+t,method:"get"})}function r(t){return Object(a["a"])({url:"get_job_list",method:"get",param:t})}function i(){return Object(a["a"])({url:"get_machine_info",method:"get"})}},"76fe":function(t,e,n){"use strict";n.d(e,"e",(function(){return l})),n.d(e,"d",(function(){return o})),n.d(e,"a",(function(){return r})),n.d(e,"b",(function(){return i})),n.d(e,"c",(function(){return c}));var a=n("b775");function l(t){return Object(a["a"])({url:"rerun_job",method:"post",data:{job_id:t}})}function o(t){return Object(a["a"])({url:"kill_job",method:"post",data:{job_id:t}})}function r(t){return Object(a["a"])({url:"copy_job",method:"post",data:{job_id:t}})}function i(t){return Object(a["a"])({url:"delete_job",method:"post",data:{job_id:t}})}function c(t){return Object(a["a"])({url:"insert_job",method:"post",data:t})}},d0a1:function(t,e,n){"use strict";n.r(e);var a=function(){var t=this,e=t.$createElement,n=t._self._c||e;return n("div",{attrs:{id:"job-list"}},[n("job-table")],1)},l=[],o=function(){var t=this,e=t.$createElement,n=t._self._c||e;return n("div",{attrs:{id:"job-table"}},[n("el-card",[n("h3",[t._v("job list")]),n("el-table",{ref:"multipleTable",attrs:{data:t.tableData},on:{"row-click":t.toJob,"selection-change":t.handleSelectionChange}},[n("el-table-column",{attrs:{type:"selection",width:"55"}}),n("el-table-column",{attrs:{prop:"id",label:"id",width:"40"}}),n("el-table-column",{attrs:{prop:"job_type",label:"job_type",width:"100"}}),n("el-table-column",{attrs:{prop:"batch",label:"batch",width:"100"}}),n("el-table-column",{attrs:{prop:"priority",label:"priority",width:"100"}}),n("el-table-column",{attrs:{prop:"limit_count",label:"limit_count",width:"100"}}),n("el-table-column",{attrs:{prop:"tag",label:"tag",width:"100"}}),n("el-table-column",{attrs:{prop:"input_data",label:"input_data",width:"100"},scopedSlots:t._u([{key:"default",fn:function(e){return[n("el-popover",{attrs:{placement:"top-start",title:"input_data",width:"300",trigger:"hover",content:e.row.input_data}},[n("el-button",{attrs:{slot:"reference"},slot:"reference"},[t._v("data")])],1)]}}])}),n("el-table-column",{attrs:{prop:"result",label:"result",width:"100"}}),n("el-table-column",{attrs:{prop:"return_count",label:"return_count",width:"100"}}),n("el-table-column",{attrs:{prop:"spend_time",label:"spend_time",width:"100"}}),n("el-table-column",{attrs:{prop:"status",label:"status",width:"100"}}),n("el-table-column",{attrs:{prop:"machine_id",label:"machine_id",width:"100"}}),n("el-table-column",{attrs:{prop:"create_time",label:"create_time",width:"100"}}),n("el-table-column",{attrs:{prop:"update_time",label:"update_time",width:"100"}})],1),n("el-pagination",{attrs:{"current-page":t.currentPage,"page-size":10,layout:"total, prev, pager, next",total:t.data.length},on:{"update:currentPage":function(e){t.currentPage=e},"update:current-page":function(e){t.currentPage=e},"current-change":t.handleCurrentChange}}),n("el-row",[n("el-col",{attrs:{span:6}},[n("el-button",{nativeOn:{click:function(e){return t.rerun(e)}}},[t._v("重跑任务")])],1),n("el-col",{attrs:{span:6}},[n("el-button",{nativeOn:{click:function(e){return t.kill(e)}}},[t._v("关闭任务")])],1),n("el-col",{attrs:{span:6}},[n("el-button",{nativeOn:{click:function(e){return t.copy(e)}}},[t._v("复制任务")])],1),n("el-col",{attrs:{span:6}},[n("el-button",{nativeOn:{click:function(e){return t.deleteTask(e)}}},[t._v("删除任务")])],1)],1)],1)],1)},r=[],i=(n("99af"),n("4160"),n("fb6a"),n("a434"),n("159b"),n("2909")),c=n("b85c"),u=n("450a"),d=n("76fe"),s={name:"JobTable",data:function(){return{currentPage:1,data:[],tableData:[],multipleSelection:[]}},created:function(){var t=this,e={job_type:"",batch:"",offset_num:0,limit_num:100};Object(u["b"])(e).then((function(e){console.log(e.data),t.data=e.data,t.tableData=t.data.slice(0,Math.min(10,t.data.length))}))},methods:{toJob:function(t){console.log(t),console.log("/details/"+t.id),this.$router.push({path:"/details",query:{id:t.id}})},toggleSelection:function(t){var e=this;t?t.forEach((function(t){e.$refs.multipleTable.toggleRowSelection(t)})):this.$refs.multipleTable.clearSelection()},handleSelectionChange:function(t){this.multipleSelection=[];var e,n=Object(c["a"])(t);try{for(n.s();!(e=n.n()).done;){var a=e.value;this.multipleSelection.push(a.id)}}catch(l){n.e(l)}finally{n.f()}console.log(this.multipleSelection)},rerun:function(){Object(d["e"])([this.data.id]).then((function(t){console.log(t.data)}))},kill:function(){Object(d["d"])([this.data.id]).then((function(t){console.log(t.data)}))},copy:function(){Object(d["a"])([this.data.id]).then((function(t){console.log(t.data)}))},deleteTask:function(){Object(d["b"])([this.data.id]).then((function(t){console.log(t.data)}))},handleCurrentChange:function(t){var e;console.log("当前页: ".concat(t)),this.tableData=[],(e=this.tableData).splice.apply(e,[0,0].concat(Object(i["a"])(this.data.slice(10*t-10,Math.min(10*t,this.data.length))))),console.log(this.tableData)}}},b=s,p=n("2877"),h=Object(p["a"])(b,o,r,!1,null,"722cb788",null),f=h.exports,m={components:{JobTable:f}},_=m,g=Object(p["a"])(_,a,l,!1,null,"691ddde7",null);e["default"]=g.exports}}]);