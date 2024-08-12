// Licensed to the .NET Foundation under one or more agreements.
// The .NET Foundation licenses this file to you under the MIT license.

var BonsaiCommon = require('./BonsaiCommon.js')

/**
 * This method will be called at the start of exports.transform in toc.html.js and toc.json.js
 */
exports.preTransform = function (model) {

  // Checks and applies TOC customisation only to API page
  if (model._key === 'api/toc.yml') {

    // Iterates through each namespace for packages with multiple namespaces
    for (namespace of model.items) {
      if (namespace.items) {
        itemsItemsLength = namespace.items.length;

        // Setups operator categories 
        let items = [{
          'name': 'Sources',
          'items': []}, {
          'name': 'Transforms',
          'items': []}, {
          'name': 'Sinks',
          'items': []}, {
          'name': 'Combinators',
          'items': []}, {
          'name': 'Helper Classes',
          'items': []}, {
          'name': 'Enums',
          'items': []         
        }];

        // Iterates through each item in the namespace and sorts them into categories
        for (let i = 0; i < itemsItemsLength; i++) {
          globalYml = '~/api/' + namespace.items[i].topicUid + '.yml';
          if (model.__global._shared[globalYml] && model.__global._shared[globalYml].type === 'class'){
            operatorType = BonsaiCommon.defineOperatorType(model.__global._shared[globalYml]);
            if (operatorType.source){
              items[0].items.push(namespace.items[i]);
            }
            else if (operatorType.transform){
              items[1].items.push(namespace.items[i]);
            }
            else if (operatorType.sink){
              items[2].items.push(namespace.items[i]);
            }
            else if (operatorType.combinator){
              items[3].items.push(namespace.items[i]);
            }
            else {
              items[4].items.push(namespace.items[i]);
            }
          }
          if (model.__global._shared[globalYml] && model.__global._shared[globalYml].type === 'enum'){
            items[5].items.push(namespace.items[i]);
          }
        }
        
        // Filters out empty TOC categories and sets namespace TOC items
        items = items.filter(item => item.items.length > 0);
        namespace.items = items;
      }
    }
  }
  return model;
}

/**
 * This method will be called at the end of exports.transform in toc.html.js and toc.json.js
 */
exports.postTransform = function (model) {
  return model;
}
