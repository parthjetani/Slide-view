function TreeView(datas, options) {
    this.root = document.createElement("div");
    this.root.className = "treeview";
    let t = this;



    var defaultOptions = {
        showAlwaysCheckBox: true,
        fold: true,
        openAllFold:false
    }

    options = Object.assign(defaultOptions, options);


    // GROUP EVENTS ---------------------

    function groupClose() {
        $(this).parent().find(">.group").slideUp("fast");
    }
    function groupToggle() {
        $(this).parent().find(">.group").slideToggle("fast");
    }

    function slideShow(){
        console.log("Hello")
    }

    /* FIRST CREATION */

    function createTreeViewReq(parentNode, datas, options) {

        for (var i = 0; i < datas.length; i++) {
            if (datas[i] != null) {
                var data = datas[i];
                var item = createSingleItem(data);
                parentNode.appendChild(item);
                if ("children" in data && data.children.length > 0) {
                    createTreeViewReq(item, data.children, options)
                }
            }
        }
    }

    function createSingleItem(data) {
        var group = document.createElement("p");
        group.className = "group"
        if ("className" in options)
            group.className += options.className;

        if ("fold" in options) {
            var foldButton = document.createElement("i");
            foldButton.className = "fa fa-angle-right";
            foldButton.setAttribute("fold-button", 1);
           
            foldButton.onclick = groupToggle.bind(foldButton);

            foldButton.isOpened = options.fold;
            
            group.appendChild(foldButton)
        }

        // ALERT ADD ICON
        var item = document.createElement("a");
        item.className = "item";
        item.setAttribute("target","_blank");
        item.setAttribute('href', '/api/only-slide/'+data.id);
        item.innerHTML = data.text;

        group.appendChild(item)
        return group;
    }

    this.update = function () {
        $(t.root).find(".group").each(function (index, el) {
            if ($(el).find(".group").length > 0) {
                $(el).find(">[fold-button]").css("visibility", "visible");
            } else {
                $(el).find(">[fold-button]").css("visibility", "hidden");
            }
        })

    }

    this.load = function (datas) {
        $(this.root).empty();
        createTreeViewReq(this.root, datas, options);
        this.update();
    }

    this.save = function (type, node) {
        if (type == null) type = "tree";

        if (type == "tree") {
            if (node == null) {
                var data = [];
                var $children = $(this.root).find(">.group");
                for (var i = 0; i < $children.length; i++) {
                    var child = this.save("tree", $children[i])
                    data.push(child)
                }
                return data;
            } else {
                var data = saveSingle($(node).find(">.item")[0]);
                data.children = []
                var $children = $(node).find(">.group");

                for (var i = 0; i < $children.length; i++) {
                    var child = this.save("tree", $children[i])
                    data.children.push(child);
                }
                return data;
            }

        }

        if (type == "list") {
            var data = [];
            var $items = $(this.root).find(".item");
            for (var i = 0; i < $items.length; i++) {
                data.push(saveSingle($items[i]));
            }
            return data;
        }
    }

    function saveSingle(el) {
        if (el == null) el = this;
        ret = Object.assign(
            { children: [] },
            el.data,
            { checked: el.checked });

        return ret;
    }

    this.load(datas);

    this.closeAllFold = function (item) {
        if (item == null) item = this.root;
        $(item).find("[fold-button]").each(function (index, el) {
            groupClose.bind(this)();
        })
    }

    this.closeAllFold();

    return this;

}
