/**
 * Created by WangCheng on 2020/9/24.
 */
function showZoomImg(domName, model) {
    var len = 0; //预览总图片数默认为零
    var domImg; //img dom
    var arrPic = new Array(); //定义一个数组src
    var arrName = new Array(); //定义一个数组name
    var num = 0; //当前预览的
    var numNow = 1; //当前预览序号,最小为1
    var leftPoint; //向左移动范围
    var rightPoint; //右移动范围
    var spin_n = 0; //旋转角度
    var zoom_n = 1;//缩放 放大

    showModel(model); //判断显示方式

    function showModel(model) {
        if(model == "img") { //图片直接查看
            $("body").on('click', domName, function() {
                domImg = $(this).parents('.zoomImgBox').find(domName);
                len = domImg.length;
                arrPic = [];
                arrName = [];
                for(var i = 0; i < len; i++) {
                    arrPic[i] = domImg.eq(i).attr("src"); //将所有img路径存储到数组中
                    if(domImg.eq(i).attr("data-caption")) {
                        arrName[i] = domImg.eq(i).attr("data-caption");
                    } else {
                        arrName[i] = '图片' + (i + 1);
                    }
                }
                var img_index = domImg.index(this); //获取点击的索引值
                num = img_index;
                numNow = num + 1;

                addMaskLater(); //添加弹出dom
            });
        } else if(model == "text") {
            $("body").on('click', domName, function() {
                domImg = $(this).children('.zoomImg-hide-box').find('img');
                len = domImg.length;
                if(len < 1) {
                    layui.use('layer', function() {
                        var layer = layui.layer;
                        layer.msg('暂未上传资料图片');
                    });
                    return;
                }
                num = 0;
                numNow = 1;
                arrPic = [];
                arrName = [];
                for(var i = 0; i < len; i++) {
                    arrPic[i] = domImg.eq(i).attr("src"); //将所有img路径存储到数组中
                    if(domImg.eq(i).attr("data-caption")) {
                        arrName[i] = domImg.eq(i).attr("data-caption");
                    } else {
                        arrName[i] = '图片' + (i + 1);
                    }

                }

                addMaskLater();
            })
        }
    }

    //给body添加弹出层的html
    function addMaskLater() {
        var maskBg =
            "<div class=\"mask-layer\">" +
            "<div class=\"mask-layer-black\"></div>" +
            "<div class=\"mask-layer-container\">" +
            "<div class=\"mask-layer-imgbox\"></div>" +
            "<div class=\"mask-layer-close\"></div>" +
            "<div class=\"img-pre\"></div>" +
            "<div class=\"img-next\"></div>" +
            "<ul class=\"contextmenu\" id='contextmenu'>" +
            "<li>" +
            "<a class=\"downimg\">下载图片</a>" +
            "</li>" +
            "<li>" +
            "<a class=\"clockwise\">顺时针旋转90°</a>" +
            "</li>" +
            "<li>" +
            "<a class=\"counterClockwise\">逆时针旋转90°</a>" +
            "</li>" +
            "</ul>" +
            "</div>" +
            "</div>";
        $("body").append(maskBg);

        if(len > 1) {
            showSmall(); //加载缩略图
        } else {
            $(".img-pre").css('display', 'none');
            $(".img-next").css('display', 'none');
        }

        showImg(); //图片加载
        showCtrl(); //插件操作
    }

    /*加载图片 及图片操作*/
    function showImg() {
        $(".mask-layer-imgbox").empty();
        var imgCont = '<div class="mask-layer-imgName">' + arrName[num] + '</div>' +
            '<div class="layer-img-box"><img src="' + arrPic[num] + '" alt=""></div>';
        $(".mask-layer-imgbox").append(imgCont);
        imgInit(); //图片操作
    }

    /*插件操作*/
    function showCtrl() {
        //上一张
        $(".img-pre").on("click", function() {
            num--;
            if(num == -1) {
                num = len - 1;
            }
            showImg();
            showSmallThis(); //显示当前选中
            initCloseEvent();
        });
        //下一张
        $(".img-next").on("click", function() {
            num++;
            if(num == len) {
                num = 0;
                boxReset();
            }
            showImg();
            showSmallThis(); //显示当前选中
            initCloseEvent();
        });
        /*关闭*/
        $(".mask-layer-close").click(function() {
            $(".mask-layer").remove();
        });

        initCloseEvent();
        function initCloseEvent(){
            $('.layer-img-box').click(function (e){
            let click_taget = $(e.target)[0].nodeName
            if(click_taget == 'IMG'){
                return
            }
            $(".mask-layer").remove();
        })
        }

        /*缩略图操作方法*/
        if(arrPic.length > 1) {
            showSmallThis(); //显示当前选中
        }
        /*缩略图当前*/
        function showSmallThis() { //显示当前选中的小图
            $('.mask-small-img').removeClass('onthis');
            $($('.mask-small-img')[num]).addClass('onthis');
            allowShow();
        }

        /*小图点击切换*/
        $('.mask-small-img').on("click", function() {
            num = $('.mask-small-img').index(this);
            showImg();
            showSmallThis(); //显示当前选中
        });

        /*box-go-left 内容向右移动*/
        $('.box-go-left').on('click', function() {
            boxGoRight();
        });

        $('.box-go-right').on('click', function() {
            boxGoLeft();
        });

        function boxGoLeft(intTime) { //向左移动
            intTime ? intTime : intTime = 1;
            if(leftPoint > 0) {
                $('.small-img-box').animate({
                    left: '-=' + 630 * intTime
                }, 500);
                leftPoint = leftPoint - intTime;
                rightPoint = rightPoint + intTime;
            }
        }

        function boxGoRight() { //向右移动
            if(rightPoint > 0) {
                $('.small-img-box').animate({
                    left: '+=630'
                }, 500);
                leftPoint++;
                rightPoint--;
            }
        }

        function allowShow() { //保持选中的图片在容器中能看到
            /*跟随切换*/
            var boxLeft = $('.small-content').offset().left; //盒子距离顶部
            var thisLeft = $('.mask-small-img.onthis').offset().left; //当前选中图片距离顶部
            var intTime = Math.floor((thisLeft - boxLeft) / 630);
            if(thisLeft - boxLeft >= 630) {
                boxGoLeft(intTime);

            } else if(thisLeft < boxLeft) {
                boxGoRight();
            } else {
                //console.log('不需移动')
            }
        }
        /*复位*/
        function boxReset() {
            $('.small-img-box').animate({
                left: '0'
            }, 500);
            leftPoint = Math.ceil(arrPic.length / 5) - 1;
            rightPoint = 0;
        }
        $(".clockwise").click(function() {
            clockwise(); //顺时针旋转
        });
        $(".counterClockwise").click(function() {
            counterClockwise(); //逆时针旋转
        })
        /*顺时针旋转*/
        function clockwise() {
            spin_n += 90;
            $(".mask-layer-imgbox img").css({
                "transform": "translate(-50%, -50%) rotate(" + spin_n + "deg) scale(" + zoom_n + ")",
                "-moz-transform": "translate(-50%, -50%) rotate(" + spin_n + "deg) scale(" + zoom_n + ")",
                "-ms-transform": "translate(-50%, -50%) rotate(" + spin_n + "deg) scale(" + zoom_n + ")",
                "-o-transform": "translate(-50%, -50%) rotate(" + spin_n + "deg) scale(" + zoom_n + ")",
                "-webkit-transform": "translate(-50%, -50%) rotate(" + spin_n + "deg) scale(" + zoom_n + ")"
            });
        };
        /*逆时针旋转*/
        function counterClockwise() {
            spin_n -= 90;
            $(".mask-layer-imgbox img").css({
                "transform": "translate(-50%, -50%) rotate(" + spin_n + "deg) scale(" + zoom_n + ")",
                "-moz-transform": "translate(-50%, -50%) rotate(" + spin_n + "deg) scale(" + zoom_n + ")",
                "-ms-transform": "translate(-50%, -50%) rotate(" + spin_n + "deg) scale(" + zoom_n + ")",
                "-o-transform": "translate(-50%, -50%) rotate(" + spin_n + "deg) scale(" + zoom_n + ")",
                "-webkit-transform": "translate(-50%, -50%) rotate(" + spin_n + "deg) scale(" + zoom_n + ")"
            });
        }
        rightMenu('.mask-layer-container');

        function rightMenu(dom) {
            // 鼠标右键事件
            $(dom).contextmenu(function(e) {
                // 获取窗口尺寸
                var winWidth = $(document).width();
                var winHeight = $(document).height();
                // 鼠标点击位置坐标
                var mouseX = e.clientX;
                var mouseY = e.clientY;
                // ul标签的宽高
                var menuWidth = $(".mask-layer .contextmenu").width();
                var menuHeight = $(".mask-layer.contextmenu").height();
                // 最小边缘margin(具体窗口边缘最小的距离)
                var minEdgeMargin = 10;
                // 以下判断用于检测ul标签出现的地方是否超出窗口范围
                // 第一种情况：右下角超出窗口
                if(mouseX + menuWidth + minEdgeMargin >= winWidth &&
                    mouseY + menuHeight + minEdgeMargin >= winHeight) {
                    menuLeft = mouseX - menuWidth - minEdgeMargin + "px";
                    menuTop = mouseY - menuHeight - minEdgeMargin + "px";
                }
                // 第二种情况：右边超出窗口
                else if(mouseX + menuWidth + minEdgeMargin >= winWidth) {
                    menuLeft = mouseX - menuWidth - minEdgeMargin + "px";
                    menuTop = mouseY + minEdgeMargin + "px";
                }
                // 第三种情况：下边超出窗口
                else if(mouseY + menuHeight + minEdgeMargin >= winHeight) {
                    menuLeft = mouseX + minEdgeMargin + "px";
                    menuTop = mouseY - menuHeight - minEdgeMargin + "px";
                }
                // 其他情况：未超出窗口
                else {
                    menuLeft = mouseX + minEdgeMargin + "px";
                    menuTop = mouseY + minEdgeMargin + "px";
                };
                // ul菜单出现
                $(".mask-layer .contextmenu").css({
                    "left": menuLeft,
                    "top": menuTop
                }).show();
                // 阻止浏览器默认的右键菜单事件
                return false;
            });
            // 点击之后，右键菜单隐藏
            $(document).click(function() {
                $(".contextmenu").hide();
            });
        }

    }

    /*图片操作方法*/
    function imgInit() {
        zoom_n = 1;//重置缩放比例
        /*图片拖拽*/
        var $div_img = $(".layer-img-box img");
        //绑定鼠标左键按住事件
        $div_img.bind("mousedown", function(event) {
            event.preventDefault && event.preventDefault(); //去掉图片拖动响应
            //获取需要拖动节点的坐标
            var offset_x = $(this)[0].offsetLeft; //x坐标
            var offset_y = $(this)[0].offsetTop; //y坐标
            //获取当前鼠标的坐标
            var mouse_x = event.pageX;
            var mouse_y = event.pageY;
            //绑定拖动事件
            //由于拖动时，可能鼠标会移出元素，所以应该使用全局（document）元素
            $(".layer-img-box").bind("mousemove", function(ev) {
                // 计算鼠标移动了的位置
                var _x = ev.pageX - mouse_x;
                var _y = ev.pageY - mouse_y;
                //设置移动后的元素坐标
                var now_x = (offset_x + _x) + "px";
                var now_y = (offset_y + _y) + "px";
                //改变目标元素的位置
                $div_img.css({
                    top: now_y,
                    left: now_x
                });
            });
            //当鼠标左键松开，接触事件绑定
            $(".layer-img-box").bind("mouseup", function() {
                $(".layer-img-box").unbind("mousemove");
            });
        });
        //绑定鼠标滚轮缩放图片
        $div_img.bind("mousewheel DOMMouseScroll", function(e) {
            e = e || window.event;
            var delta = e.originalEvent.wheelDelta || e.originalEvent.detail;
            var dir = delta > 0 ? 'down' : 'up';
            zoomImg(this, dir);
            return false;
        });

        //鼠标滚轮缩放图片
        function zoomImg(o, delta) {
            if(delta == 'up') {
                zoom_n -= 0.2;
                zoom_n = zoom_n <= 0.2 ? 0.2 : zoom_n;
            } else {
                zoom_n += 0.2;
            }
            $(".mask-layer-imgbox img").css({
                "transform": "translate(-50%, -50%) rotate(" + spin_n + "deg) scale(" + zoom_n + ")",
                "-moz-transform": "translate(-50%, -50%) rotate(" + spin_n + "deg) scale(" + zoom_n + ")",
                "-ms-transform": "translate(-50%, -50%) rotate(" + spin_n + "deg) scale(" + zoom_n + ")",
                "-o-transform": "translate(-50%, -50%) rotate(" + spin_n + "deg) scale(" + zoom_n + ")",
                "-webkit-transform": "translate(-50%, -50%) rotate(" + spin_n + "deg) scale(" + zoom_n + ")"
            });
        }
    }

    /*缩略图显示*/
    function showSmall() {
        leftPoint = Math.ceil(arrPic.length / 6) - 1;
        rightPoint = 0;

        $(".mask-layer-imgbox").addClass('has-small');
        var sDom = "<div class='small-content'><div class='small-img-box'></div></div>"
        $(".mask-layer-container").append(sDom);
        /*添加缩略图显示*/
        for(var i = 0; i < arrPic.length; i++) {
            $('.small-img-box').append('<img class="mask-small-img" src=' + arrPic[i] + '>');
        }
        if(arrPic.length > 6) { //大于六张出现左右移动按钮
            $(".small-img-box").width(Math.ceil(arrPic.length / 6) * 630);
            $('.small-content').append('<span class="box-go-left"></span><span class="box-go-right"></span>');
        }
    }
}