exports.preTransform = function (model) {
  return model;
}

exports.postTransform = function (model) {
  var visit = function (trees) {
    if (!trees) return;
    trees.forEach(function (tree) {
      if (tree.lang && tree.value) {
        visit(tree.value);
        return;
      }
      if (!tree.inheritance || tree.inheritance.length === 0) {
        tree.inheritance = [];
      } else {
        visit(tree.inheritance);
      }
    });
  };
  visit(model.inheritance);

  var sourceHref = function (item) {
    var source = item.source;
    if (Array.isArray(source)) {
      source = source.length > 0 ? source[0].value : null;
    }
    return source && source.href ? source.href : '';
  };
  model.sourceurl = model.sourceurl || sourceHref(model);
  (model.children || []).forEach(function (group) {
    (group.children || []).forEach(function (item) {
      item.sourceurl = item.sourceurl || sourceHref(item);
    });
  });
  return model;
}
