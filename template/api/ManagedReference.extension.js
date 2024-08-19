// Licensed to the .NET Foundation under one or more agreements.
// The .NET Foundation licenses this file to you under the MIT license.

var BonsaiCommon = require('./BonsaiCommon.js')

// This function is important for stripping the extra line that is present in some fields
// replace last instance of '<p' with '<p style="margin-bottom:0;"'
function removeBottomMargin(str) {
  return str
    .split('').reverse().join('')
    .replace('<p'.split('').reverse().join(''), '<p style="margin-bottom:0;"'.split('').reverse().join(''))
    .split('').reverse().join('');
}

// Strip IObservable and replace 'TSource' with 'Anything' 
function replaceIObservableAndTSource(str){
  if (str.includes('IGroupedObservable')){
    const re = new RegExp('<a.*IGroupedObservable.*&lt;');
    str = str.replace(re, '').replace('&gt;','').replace('&gt;','').replace('TSource', 'Anything');
  }
  else if (str.includes('IObservable')){
    const re = new RegExp('<a.*IObservable.*&lt;');
    str = str.replace(re, '').replace('&gt;','').replace('TSource', 'Anything');
    // can't combine re and '&gt;' into the same regex and do replaceAll because some classes have have two '&gt' in which case one of them is necessary
  }
  return str;
}

// compile list of data for input --> o --> output diagrams
function defineInputsAndOutputs(model){
  operators = [];
  if (model.children){
    const childrenLength = model.children.length;
    for (let i = 0; i < childrenLength; i++){
      if (model.children[i].uid.includes('Generate') || model.children[i].uid.includes('Process')){
        description = [model.children[i].summary, model.children[i].remarks].join('');
        input = {};
        if (model.children[i].syntax.parameters && model.children[i].syntax.parameters[0]){
          input = {
            'specName': replaceIObservableAndTSource(model.children[i].syntax.parameters[0].type.specName[0].value),
            'name': model.children[i].syntax.parameters[0].type.name[0].value.replaceAll(/(IObservable<)|(>)/g, ''),
            'description': removeBottomMargin([model.children[i].syntax.parameters[0].description, model.children[i].syntax.parameters[0].remarks].join(''))
          };
          input.external = true;
        }
        if (model.children[i].syntax.return){
          output = {
            'specName': replaceIObservableAndTSource(model.children[i].syntax.return.type.specName[0].value),
            'name': model.children[i].syntax.return.type.name[0].value.replaceAll(/(IObservable<)|(>)/g, ''),
            'description': removeBottomMargin([model.children[i].syntax.return.description, model.children[i].syntax.return.remarks].join(''))};
          outputYml = [ '~/api/', 
                        model.children[i].syntax.return.type.uid.replaceAll(/(\D*{)|(}$)/g, ''),  
                        '.yml'].join('');
          if (model['__global']['_shared'][outputYml] && model['__global']['_shared'][outputYml]['children'] && (model['__global']['_shared'][outputYml].type === 'class')){
            output.internal = true;
          }
          else if (!output.internal){
            output.external = true;
          }
        }
        if (Object.keys(input).length){
          operators.push({'description': description, 'input': input, 'output': output, 'hasInput': true});
        }
        else {
          operators.push({'description': description, 'output': output});
        }
      }
    }
  }
  return operators;
}

// compile list of properties
function defineProperties(model){
  properties = [];
  if (model.children){
    const childrenLength = model.children.length;
    for (let i = 0; i < childrenLength; i++){
      if (model.children[i].type === 'property'){

        // This section adds enum fields and values to the property table if the property is an enum
        // However doesnt always work (In Pulsepal Repo - Outputchannel enum doesnt show sometimes but the others do)
        // Bug present in original template so need to troubleshoot
        // Nice to have I think but not critical.
        potentialEnumYml = '~/api/' + model['children'][i].syntax.return.type.uid + '.yml';
        let enumFields = [];
        if (model['__global']['_shared'][potentialEnumYml] && (model['__global']['_shared'][potentialEnumYml]['type'] === 'enum')){
          enumFields = defineEnumFields(model['__global']['_shared'][potentialEnumYml]);
        }
        if (enumFields.length > 0){
          properties.push({
            'name': model.children[i].name[0].value, 
            'type': model.children[i].syntax.return.type.specName[0].value, 
            'description': removeBottomMargin([model.children[i].summary, model.children[i].remarks].join('')),
            'enumFields': enumFields,
            'hasEnum': true
          });
        }
        // This adds the rest of the non-enum properties normally
        else { 
          properties.push({
            'name': model.children[i].name[0].value, 
            'type': model.children[i].syntax.return.type.specName[0].value, 
            'description': removeBottomMargin([model.children[i].summary, model.children[i].remarks].join(''))
          });
        }
      }
    }
  }
  // This adds properties that belong to the members that it inherits (and which show up in the Bonsai side panel)
  // On a default docfx website they dont show, so its pretty important.
  if (model.inheritedMembers){
    const inheritedMembersLength = model.inheritedMembers.length;
    for (let i = 0; i < inheritedMembersLength; i++){
      if (model.inheritedMembers[i].type && (model.inheritedMembers[i].type === 'property')){
        let inheritedMemberYml = '~/api/' + model.inheritedMembers[i].parent + '.yml';
        if (model['__global']['_shared'][inheritedMemberYml]['children']){
          let inheritedMemberChildrenLength = model['__global']['_shared'][inheritedMemberYml]['children'].length;
          for (let j =  0; j < inheritedMemberChildrenLength; j++){
            if (model.inheritedMembers[i].uid === model['__global']['_shared'][inheritedMemberYml]['children'][j].uid){
              properties.push(
                {'name': model.inheritedMembers[i].name[0].value, 
                'type': model['__global']['_shared'][inheritedMemberYml]['children'][j].syntax.return.type.specName[0].value, 
                'description':  removeBottomMargin([model['__global']['_shared'][inheritedMemberYml]['children'][j].summary, 
                                                    model['__global']['_shared'][inheritedMemberYml]['children'][j].remarks].join(''))
              });
            }
          }
        }
      }
    }
  }
  return properties;
}

// While docfx has an option to sort enum fields alphabetically, it does not have a similar option for class properties
// and this function provides that.
function sortProperties(properties){
  let propertyNames = [];
  let propertyNamesThatFitPattern = [];
  const propertiesLength = properties.length;
  for (let i = 0; i < propertiesLength; i++){
    propertyNames.push([properties[i].name, 
                        /\D+\d+$/.test(properties[i].name), 
                        String(properties[i].name.match(/\D+/)), 
                        Number(properties[i].name.match(/\d+$/))]);
  }
  for (let i = 0; i < propertiesLength; i++){
    if (propertyNames[i][1]){
      if (!propertyNamesThatFitPattern.includes(propertyNames[i][2])){
        propertyNamesThatFitPattern.push(propertyNames[i][2]);
      }
    }
  }
  const propertyNamesThatFitPatternLength = propertyNamesThatFitPattern.length;
  for (let j = 0; j < propertyNamesThatFitPatternLength; j++){
    for (let i = 1; i < propertiesLength; i++){
      for (let k = i; k > 0; k--){
        if ((propertyNames[k][2] === propertyNamesThatFitPattern[j]) && (propertyNames[k - 1][2] === propertyNamesThatFitPattern[j])){
          if (propertyNames[k][3] < propertyNames[k - 1][3]){
            swapElements(properties, k, k - 1);
            swapElements(propertyNames, k, k - 1); // why does this need to be here for this sortProperties function to work?
          }
        }
      }
    }
  }
  return properties;
}

const swapElements = (array, index1, index2) => {
  const temp = array[index1];
  array[index1] = array[index2];
  array[index2] = temp;
};

// While enum fields can be accessed directly using the mustache template, this function is
// still important for stripping the extra line that is present in the summary/remarks field
function defineEnumFields(model){
  let enumFields = [];
  if (model.children){
    const childrenLength = model.children.length;
    for (let i = 0; i < childrenLength; i++){
      if (model.children[i].type === 'field'){
        enumFields.push({
          'field&value': model.children[i].syntax.content[0].value,
          'description': removeBottomMargin([ model.children[i].summary, 
                                              model.children[i].remarks].join(''))
        });
      }
    }
  }
  return enumFields;
}


/**
 * This method will be called at the start of exports.transform in ManagedReference.html.primary.js
 */
exports.preTransform = function (model) {
  
  model.bonsai = {};
  
  model.bonsai.description = [model.summary, model.remarks].join('');

  operatorType = BonsaiCommon.defineOperatorType(model);
  
  if (operatorType.type){
    model.bonsai.operatorType = operatorType.type
  }

  if (operatorType.showWorkflow) {
    model.bonsai.showWorkflow = operatorType.showWorkflow;
  }
  
  operators = defineInputsAndOutputs(model);
  if (operators.length > 0){
    model.bonsai.operators = operators;
  }

  properties = defineProperties(model);
  if (properties.length > 0){
    model.bonsai.hasProperties = true;
    model.bonsai.properties = sortProperties(properties);
  }

  enumFields = defineEnumFields(model);
  if (enumFields.length > 0){
    model.bonsai.hasEnumFields = true;
    model.bonsai.enumFields = enumFields;
  }

  return model;
}

/**
 * This method will be called at the end of exports.transform in ManagedReference.html.primary.js
 */
exports.postTransform = function (model) {
  return model;
}