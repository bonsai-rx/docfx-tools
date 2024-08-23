// Licensed to the .NET Foundation under one or more agreements.
// The .NET Foundation licenses this file to you under the MIT license.

function defineOperatorType(model){
  // Define Bonsai operator types in documentation by checking for an explicit Category tag. If the class does not provide one,
  // check the inheritance tree of the class. 

  const checkForCategory = (category) => model.syntax?.content[0].value.includes(`[WorkflowElementCategory(ElementCategory.${category})]`);
  const checkInheritance = (inheritance) => model.inheritance?.some(inherited => inherited.uid.includes(inheritance));

  source = checkForCategory('Source') || checkInheritance('Bonsai.Source');
  sink = checkForCategory('Sink') || checkInheritance('Bonsai.Sink') || checkInheritance('Bonsai.IO.StreamSink') || checkInheritance('Bonsai.IO.FileSink');
  combinator = checkForCategory('Combinator') || checkInheritance('Bonsai.Combinator') || checkInheritance('Bonsai.WindowCombinator');
  transform = checkForCategory('Transform') || checkInheritance('Bonsai.Transform') || checkInheritance('Bonsai.Transform');

  let operatorType = {}
  operatorType.type = sink ? 'sink' : source ? 'source' : transform ? 'transform' : combinator ? 'combinator' :  false ; 

  return operatorType;
}

/**
 * This method will be called at the start of exports.transform in toc.html.js and toc.json.js
 */
exports.preTransform = function (model) {

  // Checks and applies TOC customisation only to API page
  if (model._key === 'api/toc.yml') {

  //Setups operator mapping
  const typeIndexMap = {
    'source': 0,
    'transform': 1,
    'sink': 2,
    'combinator': 3
  };

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
            operatorType = defineOperatorType(model.__global._shared[globalYml]);

            const index = typeIndexMap[operatorType.type]
            if (index !== undefined) {
              items[index].items.push(namespace.items[i]);
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
